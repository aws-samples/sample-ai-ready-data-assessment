#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Release-readiness gate for the AI-Ready Data assessment.

Separate from the unit tests on purpose. The unit tests answer "does the tool
work"; this answers "is this checkout fit to be published". It is the gate that
catches the class of mistake that only matters at publication time:

1. **Unreplaced placeholders.** An owner placeholder stands in for the GitHub org
   until the repository has a home. Shipping it produces dead links in
   CITATION.cff, the README badges, and the clone command in CONTRIBUTING.
2. **Internal references.** An internal host name, ticket tracker, or corporate
   URL that was fine in a private working copy becomes a leak the moment the
   repository is public. This is the check that catches an internal git remote
   left behind in ``CITATION.cff`` or a clone command in ``CONTRIBUTING.md``.
3. **Version drift.** ``VERSION``, the README badges, and ``CITATION.cff`` must
   state the same questionnaire version.
4. **Committed local artifacts.** A stray ``.DS_Store``, a real answers file, or
   a generated ``test/results/`` directory should never reach a public repo —
   an answers file in particular describes a real organization's weak spots.
   Only files git actually tracks are checked, so an untracked local scratch
   file or a gitignored artifact does not block a release.
5. **Missing license headers.** Every ``.py`` file must carry the SPDX header,
   because that is what an open-source review looks for first.

Run it before tagging a release:  python3 scripts/check_release_ready.py

Exits 0 when the checkout is publishable, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Placeholders that must be replaced before the repository is published.
#: Assembled rather than written literally so this file does not match itself.
PLACEHOLDERS = ("<" + "OWNER>",)

#: The public home of this repository. Referenced by the internal-reference
#: check's error message so the fix is obvious.
PUBLIC_REPO_URL = "https://github.com/aws-samples/sample-ai-ready-data-assessment"

#: Substrings that betray an internal-only reference, as (needle, why) pairs.
#: Assembled from fragments so this file does not match itself.
INTERNAL_MARKERS = (
    ("gitlab." + "aws.dev", "internal AWS GitLab host"),
    ("code." + "amazon.com", "internal Amazon code host"),
    ("issues." + "amazon.com", "internal Amazon issue tracker"),
    ("tiny." + "amazon.com", "internal Amazon link shortener"),
    ("quip-" + "amazon.com", "internal Amazon document host"),
    ("broadcast." + "amazon.com", "internal Amazon video host"),
    ("w." + "amazon.com", "internal Amazon wiki"),
    ("isengard", "internal AWS account-management tool"),
    ("midway-" + "auth", "internal Amazon authentication"),
    (".corp." + "amazon.com", "internal Amazon corporate host"),
    (".ant." + "amazon.com", "internal Amazon corporate host"),
)

#: Files exempt from the placeholder / internal-marker scan because they define
#: or document those very strings.
PLACEHOLDER_SCAN_EXEMPT = frozenset({"scripts/check_release_ready.py"})

#: Files that must all state the same questionnaire version.
VERSION_BADGE_FILES = ("README.md", "README.zh.md")

#: Paths that must not be committed, as (glob, why) pairs.
FORBIDDEN = (
    ("**/.DS_Store", "macOS directory metadata"),
    ("**/._*", "macOS resource forks (from unzipping an archive on macOS)"),
    ("test/results/**", "generated test artifacts (machine-specific)"),
)

#: Documentation that must exist, in both locales where applicable.
REQUIRED_FILES = (
    "README.md",
    "README.zh.md",
    "SCORING.md",
    "SCORING.zh.md",
    "CONTRIBUTING.md",
    "CONTRIBUTING.zh.md",
    "CODE_OF_CONDUCT.md",
    "CODE_OF_CONDUCT.zh.md",
    "SECURITY.md",
    "SECURITY.zh.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE",
    "LICENSE-CONTENT",
    "NOTICE",
    "VERSION",
    # SECURITY.md and both READMEs promise these exist; a missing .gitignore in
    # particular means the documented protection for a real answers file is a
    # promise the repository does not keep.
    ".gitignore",
    ".github/workflows/ci.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/question_proposal.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/dependabot.yml",
)

#: Text files worth scanning for placeholders.
SCAN_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".cff", ".txt"}

#: The SPDX header line every Python file must carry.
SPDX_LINE = "SPDX-License-Identifier: Apache-2.0"


def _git_tracked() -> set[str] | None:
    """Return repo-relative paths git tracks, or None when git is unavailable.

    Used so that gitignored artifacts and untracked local scratch files do not
    block a release -- only what would actually be published is checked.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return {p for p in proc.stdout.decode("utf-8").split("\0") if p}


def _text_files() -> list[Path]:
    """Return candidate text files, skipping caches and generated output."""
    skip_parts = {".git", "__pycache__", ".venv", "venv", "results"}
    out = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if skip_parts & set(path.relative_to(REPO_ROOT).parts):
            continue
        out.append(path)
    return out


def check_placeholders(errors: list[str]) -> None:
    for path in _text_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in PLACEHOLDER_SCAN_EXEMPT:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for placeholder in PLACEHOLDERS:
            if placeholder in text:
                lines = [
                    i
                    for i, line in enumerate(text.splitlines(), 1)
                    if placeholder in line
                ]
                errors.append(
                    f"{rel}: unreplaced placeholder {placeholder} on "
                    f"line(s) {lines} -- substitute the real GitHub owner"
                )


def check_internal_references(errors: list[str]) -> None:
    """Flag internal-only host names and URLs.

    These are the mistakes that are invisible in a private working copy and
    permanent once the repository is public: an internal git remote in
    ``CITATION.cff``, an internal clone command in ``CONTRIBUTING.md``.
    """
    for path in _text_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in PLACEHOLDER_SCAN_EXEMPT:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for needle, why in INTERNAL_MARKERS:
            if needle not in lowered:
                continue
            lines = [
                i
                for i, line in enumerate(text.splitlines(), 1)
                if needle in line.lower()
            ]
            errors.append(
                f"{rel}: internal reference {needle!r} ({why}) on line(s) "
                f"{lines} -- must not be published; the public home is "
                f"{PUBLIC_REPO_URL}"
            )


def check_license_headers(errors: list[str]) -> None:
    """Every tracked Python file must carry the SPDX license header."""
    tracked = _git_tracked()
    for path in sorted(REPO_ROOT.rglob("*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        if tracked is not None and rel not in tracked:
            continue
        # The header lives in the first few lines, after any shebang.
        head = "".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[:5])
        if SPDX_LINE not in head:
            errors.append(f"{rel}: missing '{SPDX_LINE}' header")


def check_versions(errors: list[str]) -> None:
    version_file = REPO_ROOT / "VERSION"
    if not version_file.is_file():
        errors.append("VERSION file is missing")
        return
    version = version_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"VERSION {version!r} is not a MAJOR.MINOR.PATCH version")

    for name in VERSION_BADGE_FILES:
        path = REPO_ROOT / name
        if not path.is_file():
            continue
        badges = re.findall(
            r"questionnaire-v(\d+\.\d+\.\d+)", path.read_text(encoding="utf-8")
        )
        if not badges:
            errors.append(f"{name}: no questionnaire version badge found")
        for badge in badges:
            if badge != version:
                errors.append(
                    f"{name}: badge says v{badge} but VERSION says {version}"
                )

    citation = REPO_ROOT / "CITATION.cff"
    if citation.is_file():
        match = re.search(
            r"^version:\s*(\S+)", citation.read_text(encoding="utf-8"), re.M
        )
        if match is None:
            errors.append("CITATION.cff: no version field")
        elif match.group(1).strip('"') != version:
            errors.append(
                f"CITATION.cff: version {match.group(1)} but VERSION says {version}"
            )


def check_forbidden(errors: list[str]) -> None:
    """Flag artifacts that must not be published.

    Scoped to git-tracked files: a gitignored ``test/results/`` or a local
    ``my-answers.csv`` is expected to exist in a working checkout and is not a
    release problem. When git is unavailable the check is skipped rather than
    guessed at, and says so.
    """
    tracked = _git_tracked()
    if tracked is None:
        print(
            "note: git unavailable -- skipping the committed-artifact check",
            file=sys.stderr,
        )
        return

    for pattern, why in FORBIDDEN:
        for path in REPO_ROOT.glob(pattern):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if path.is_file() and rel in tracked:
                errors.append(f"{rel}: must not be committed ({why})")

    # A real answers file is a disclosure risk, not just clutter.
    for rel in sorted(tracked):
        name = Path(rel).name
        if not re.search(r"answers.*\.(csv|json)\Z", name, re.IGNORECASE):
            continue
        if name.startswith("answers.example."):
            continue
        errors.append(
            f"{rel}: looks like a real answers file -- it describes an "
            "organization's weak spots and must not be published"
        )


def check_required_files(errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (REPO_ROOT / name).is_file():
            errors.append(f"{name}: required file is missing")


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_placeholders(errors)
    check_internal_references(errors)
    check_license_headers(errors)
    check_versions(errors)
    check_forbidden(errors)

    if errors:
        print("Release readiness check FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            f"\n{len(errors)} problem(s) must be resolved before publishing.",
            file=sys.stderr,
        )
        return 1

    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print(
        f"Release readiness OK: questionnaire v{version}, no placeholders, no "
        "internal references, SPDX headers present, no version drift, no "
        "committed local artifacts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
