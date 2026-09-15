#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Repository integrity checks for the AI-Ready Data assessment.

Validates that each module file's YAML front-matter ``question_count`` matches
the actual number of ``### Q`` headings, that each dimension has the expected
number of questions (6/12/12/5/5/5 = 45 total), and that every question exposes
exactly the five options A/B/C/D/N-A.

Also validates **cross-locale parity**: every locale must ship the same module
filenames, carrying the same dimension ids and the same question counts. A
translation that silently drops or gains a question would otherwise make the
two locales score differently while both passed their own checks.

Exits non-zero on any violation so CI fails loudly. Standard library only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = REPO_ROOT / "modules"

# Expected question count per dimension id.
EXPECTED_COUNTS = {
    "dim1": 6,
    "dim2": 12,
    "dim3": 12,
    "dim4": 5,
    "dim5": 5,
    "dim6": 5,
}
EXPECTED_TOTAL = 45

Q_HEADING = re.compile(r"^###\s+Q(\d+)\s*$", re.MULTILINE)
OPTION_LINE = re.compile(r"^-\s*(A|B|C|D|N/A)\.\s", re.MULTILINE)
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
#: The bold stem line repeats the question number, e.g. '**Q3. Do the ...?**'.
#: It must agree with its '### Q3' heading -- the number is written twice, so
#: renumbering a dimension can easily update one and not the other.
Q_STEM = re.compile(r"^\*\*Q(\d+)\.", re.MULTILINE)


def parse_front_matter(text: str) -> dict[str, str]:
    m = FRONT_MATTER.match(text)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def check_module(path: Path, errors: list[str]) -> tuple[str | None, int]:
    text = path.read_text(encoding="utf-8")
    fm = parse_front_matter(text)
    if not fm:
        errors.append(f"{path.name}: missing YAML front-matter")
        return None, 0

    dim_id = fm.get("id")
    q_headings = Q_HEADING.findall(text)
    actual = len(q_headings)

    # front-matter question_count must match actual headings
    declared = fm.get("question_count")
    if declared is None:
        errors.append(f"{path.name}: front-matter missing question_count")
    elif declared.isdigit() and int(declared) != actual:
        errors.append(
            f"{path.name}: front-matter question_count={declared} "
            f"but found {actual} '### Q' headings"
        )

    # question numbers must be 1..actual, in order, no gaps/dupes
    nums = [int(n) for n in q_headings]
    if nums != list(range(1, actual + 1)):
        errors.append(
            f"{path.name}: question numbers not a clean 1..{actual} sequence: {nums}"
        )

    # expected count for this dimension
    if dim_id in EXPECTED_COUNTS and actual != EXPECTED_COUNTS[dim_id]:
        errors.append(
            f"{path.name}: dimension {dim_id} expected "
            f"{EXPECTED_COUNTS[dim_id]} questions, found {actual}"
        )

    # each question block must carry exactly the 5 option letters
    blocks = re.split(r"^###\s+Q\d+\s*$", text, flags=re.MULTILINE)[1:]
    for idx, block in enumerate(blocks, start=1):
        # The stem repeats the question number; it must match its heading.
        stem = Q_STEM.search(block)
        if stem is None:
            errors.append(
                f"{path.name} Q{idx}: no bold stem line -- expected '**Q{idx}. ...**'"
            )
        elif int(stem.group(1)) != idx:
            errors.append(
                f"{path.name} Q{idx}: heading says Q{idx} but the stem says "
                f"Q{stem.group(1)} -- the two must agree"
            )

        opts = set(OPTION_LINE.findall(block))
        expected = {"A", "B", "C", "D", "N/A"}
        if opts != expected:
            missing = expected - opts
            extra = opts - expected
            detail = []
            if missing:
                detail.append(f"missing {sorted(missing)}")
            if extra:
                detail.append(f"unexpected {sorted(extra)}")
            errors.append(f"{path.name} Q{idx}: options {'; '.join(detail)}")

    return dim_id, actual


def main() -> int:
    errors: list[str] = []
    if not MODULES_DIR.is_dir():
        print(f"ERROR: {MODULES_DIR} not found", file=sys.stderr)
        return 2

    dirs = [MODULES_DIR]
    zh_dir = REPO_ROOT / "zh" / "modules"
    if zh_dir.is_dir():
        dirs.append(zh_dir)

    checked = 0
    # locale dir -> {filename: (dim_id, question_count)}, for the parity check.
    per_locale: dict[str, dict[str, tuple[str | None, int]]] = {}
    for mod_dir in dirs:
        rel = mod_dir.relative_to(REPO_ROOT)
        files = sorted(mod_dir.glob("*.md"))
        total = 0
        seen: set[str] = set()
        shape: dict[str, tuple[str | None, int]] = {}
        for path in files:
            dim_id, count = check_module(path, errors)
            total += count
            shape[path.name] = (dim_id, count)
            if dim_id:
                seen.add(dim_id)
        per_locale[str(rel)] = shape

        if total != EXPECTED_TOTAL:
            errors.append(f"{rel}: total questions = {total}, expected {EXPECTED_TOTAL}")
        missing_dims = set(EXPECTED_COUNTS) - seen
        if missing_dims:
            errors.append(f"{rel}: missing dimension modules: {sorted(missing_dims)}")
        checked += len(files)

    # Cross-locale parity: same filenames, same dim ids, same question counts.
    locales = sorted(per_locale)
    if len(locales) > 1:
        base_name, base = locales[0], per_locale[locales[0]]
        for other_name in locales[1:]:
            other = per_locale[other_name]
            only_base = sorted(set(base) - set(other))
            only_other = sorted(set(other) - set(base))
            if only_base:
                errors.append(
                    f"locale parity: {only_base} present in {base_name} "
                    f"but missing from {other_name}"
                )
            if only_other:
                errors.append(
                    f"locale parity: {only_other} present in {other_name} "
                    f"but missing from {base_name}"
                )
            for name in sorted(set(base) & set(other)):
                if base[name] != other[name]:
                    errors.append(
                        f"locale parity: {name} is (id={base[name][0]}, "
                        f"questions={base[name][1]}) in {base_name} but "
                        f"(id={other[name][0]}, questions={other[name][1]}) "
                        f"in {other_name}"
                    )

    if errors:
        print("Integrity check FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"Integrity check OK: {checked} module file(s) across "
        f"{len(dirs)} locale(s), {EXPECTED_TOTAL} questions each."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
