#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the questionnaire integrity checker (``scripts/check_modules.py``).

Covers front-matter parsing, per-question option validation, question numbering,
and the real repository content for both locales (``modules/`` and ``zh/modules/``).
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("scoring", "scripts"):
    _p = str(_REPO_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_modules


VALID_QUESTION = """### Q{n}
**Q{n}. Some question text?**

- A. not started
- B. initial
- C. basic
- D. mature
- N/A. not applicable
"""


def _module_text(dim_id: str, count: int, title: str = "T") -> str:
    """Build a syntactically valid module file body with ``count`` questions."""
    head = (
        "---\n"
        f"id: {dim_id}\n"
        f"title: {title}\n"
        f"dimension_number: {dim_id[-1]}\n"
        f"question_count: {count}\n"
        "---\n\nIntro paragraph.\n\n"
    )
    body = "\n".join(VALID_QUESTION.format(n=i) for i in range(1, count + 1))
    return head + body


class TestFrontMatter(unittest.TestCase):
    def test_parses_key_values(self) -> None:
        fm = check_modules.parse_front_matter(_module_text("dim1", 6))
        self.assertEqual(fm["id"], "dim1")
        self.assertEqual(fm["question_count"], "6")

    def test_missing_front_matter_returns_empty(self) -> None:
        self.assertEqual(check_modules.parse_front_matter("# no front matter\n"), {})


class TestCheckModule(unittest.TestCase):
    """``check_module`` appends human-readable strings to an errors list."""

    def _check(self, text: str, name: str = "01-x.md"):
        path = Path(self.tmp) / name
        path.write_text(text, encoding="utf-8")
        errors: list[str] = []
        dim_id, count = check_modules.check_module(path, errors)
        return dim_id, count, errors

    def setUp(self) -> None:
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self._tmpdir.name

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_valid_module_has_no_errors(self) -> None:
        dim_id, count, errors = self._check(_module_text("dim1", 6))
        self.assertEqual(dim_id, "dim1")
        self.assertEqual(count, 6)
        self.assertEqual(errors, [])

    def test_missing_front_matter_is_reported(self) -> None:
        _, _, errors = self._check("### Q1\n- A. x\n")
        self.assertTrue(any("front-matter" in e for e in errors))

    def test_declared_count_mismatch_is_reported(self) -> None:
        text = _module_text("dim1", 6).replace("question_count: 6", "question_count: 7")
        _, _, errors = self._check(text)
        self.assertTrue(any("question_count=7" in e for e in errors))

    def test_wrong_count_for_dimension_is_reported(self) -> None:
        # dim1 must have 6 questions; give it 5.
        _, _, errors = self._check(_module_text("dim1", 5))
        self.assertTrue(
            any("expected 6 questions" in e for e in errors), msg=str(errors)
        )

    def test_missing_option_is_reported(self) -> None:
        text = _module_text("dim1", 6).replace("- D. mature\n", "", 1)
        _, _, errors = self._check(text)
        self.assertTrue(any("missing" in e and "D" in e for e in errors), msg=str(errors))

    def test_non_sequential_numbering_is_reported(self) -> None:
        text = _module_text("dim1", 6).replace("### Q3", "### Q9", 1)
        _, _, errors = self._check(text)
        self.assertTrue(any("sequence" in e for e in errors), msg=str(errors))

    def test_stem_number_disagreeing_with_heading_is_reported(self) -> None:
        # The question number is written twice -- once in the '### Q3' heading
        # and once in the '**Q3. ...**' stem -- so renumbering a dimension can
        # update one and miss the other.
        text = _module_text("dim1", 6).replace("**Q3.", "**Q9.", 1)
        _, _, errors = self._check(text)
        self.assertTrue(
            any("stem says Q9" in e for e in errors), msg=str(errors)
        )

    def test_missing_stem_line_is_reported(self) -> None:
        text = _module_text("dim1", 6).replace("**Q3. Some question text?**\n", "", 1)
        _, _, errors = self._check(text)
        self.assertTrue(
            any("no bold stem line" in e for e in errors), msg=str(errors)
        )


class TestRealRepositoryContent(unittest.TestCase):
    """The checked-in questionnaire must pass its own integrity gate."""

    EXPECTED = {
        "01-cost-and-business-value.md": 6,
        "02-data-foundation-and-quality.md": 12,
        "03-platform-architecture-and-ops.md": 12,
        "04-organization-and-talent.md": 5,
        "05-governance-and-trust.md": 5,
        "06-security-and-compliance.md": 5,
    }

    def test_expected_total_is_45(self) -> None:
        self.assertEqual(sum(self.EXPECTED.values()), 45)
        self.assertEqual(check_modules.EXPECTED_TOTAL, 45)

    def test_both_locales_present_and_valid(self) -> None:
        for rel in ("modules", "zh/modules"):
            mod_dir = _REPO_ROOT / rel
            with self.subTest(locale=rel):
                self.assertTrue(mod_dir.is_dir(), f"{rel} missing")
                errors: list[str] = []
                total = 0
                for name, expected_count in self.EXPECTED.items():
                    path = mod_dir / name
                    self.assertTrue(path.is_file(), f"{rel}/{name} missing")
                    _, count = check_modules.check_module(path, errors)
                    self.assertEqual(
                        count, expected_count, f"{rel}/{name} question count"
                    )
                    total += count
                self.assertEqual(total, 45, f"{rel} total")
                self.assertEqual(errors, [], f"{rel} errors: {errors}")

    def test_main_exits_zero_on_real_content(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = check_modules.main()
        self.assertEqual(rc, 0, f"stderr: {err.getvalue()}")
        self.assertIn("Integrity check OK", out.getvalue())
        # both locales are covered by the run
        self.assertIn("locale", out.getvalue())


class TestCrossLocaleParity(unittest.TestCase):
    """Every locale must ship the same modules with the same question counts.

    A translation that silently drops or gains a question would otherwise let
    the two locales score differently while each passed its own count check.
    """

    LOCALES = ("modules", "zh/modules")

    def _shape(self, rel: str) -> dict[str, tuple[str | None, int]]:
        errors: list[str] = []
        shape = {}
        for path in sorted((_REPO_ROOT / rel).glob("*.md")):
            shape[path.name] = check_modules.check_module(path, errors)
        return shape

    def test_same_filenames_across_locales(self) -> None:
        shapes = [set(self._shape(rel)) for rel in self.LOCALES]
        self.assertEqual(
            shapes[0],
            shapes[1],
            "modules/ and zh/modules/ must contain the same filenames",
        )

    def test_same_dim_ids_and_counts_across_locales(self) -> None:
        en, zh = (self._shape(rel) for rel in self.LOCALES)
        self.assertEqual(
            en, zh, "each module must carry the same id and question count in both locales"
        )

    def test_checker_detects_a_parity_break(self) -> None:
        # Drop one question from a locale copy and confirm the parity check
        # fires, even though each locale still looks internally coherent.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in self.LOCALES:
                (root / rel).mkdir(parents=True)
                for name, count in TestRealRepositoryContent.EXPECTED.items():
                    dim = f"dim{name[1]}"
                    # zh copy of dim6 loses a question AND declares the lower
                    # count, so it is self-consistent but out of parity.
                    n = count - 1 if (rel == "zh/modules" and dim == "dim6") else count
                    (root / rel / name).write_text(
                        _module_text(dim, n), encoding="utf-8"
                    )
            original = check_modules.REPO_ROOT
            try:
                check_modules.REPO_ROOT = root
                check_modules.MODULES_DIR = root / "modules"
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    rc = check_modules.main()
            finally:
                check_modules.REPO_ROOT = original
                check_modules.MODULES_DIR = original / "modules"
            self.assertEqual(rc, 1)
            self.assertIn("locale parity", err.getvalue())


if __name__ == "__main__":
    unittest.main()
