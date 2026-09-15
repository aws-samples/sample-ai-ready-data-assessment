#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Guard tests that keep the documentation honest.

These exist because documentation drifts silently: a sample report pasted into
the README stays frozen while the code that produces it changes. Each test here
compares a doc artifact against the real thing rather than against a
hand-maintained copy.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("scoring", "scripts"):
    _p = str(_REPO_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import score

EXAMPLE_CSV = _REPO_ROOT / "scoring" / "answers.example.csv"

#: (README file, the marker line the sample block follows, the --lang it shows)
SAMPLE_BLOCKS = [
    ("README.md", "Example output:", "en"),
    ("README.zh.md", "中文输出示例", "zh"),
]

CJK = re.compile(r"[\u4e00-\u9fff]")


def _first_fence_after(text: str, marker: str) -> str:
    """Return the contents of the first ``` fenced block after ``marker``."""
    idx = text.index(marker)
    match = re.search(r"```\n(.*?)```", text[idx:], re.S)
    if match is None:
        raise AssertionError(f"no fenced block found after {marker!r}")
    return match.group(1).rstrip("\n")


class TestReadmeSampleOutput(unittest.TestCase):
    """The sample report in each README must be what the script actually prints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = score.score_answers(score.load_answers(str(EXAMPLE_CSV)))
        # Same version the CLI stamps, so the comparison covers that line too.
        cls.version = score.read_questionnaire_version()

    def test_sample_blocks_match_real_output(self) -> None:
        for readme, marker, lang in SAMPLE_BLOCKS:
            with self.subTest(readme=readme, lang=lang):
                path = _REPO_ROOT / readme
                self.assertTrue(path.is_file(), f"{readme} missing")
                documented = _first_fence_after(
                    path.read_text(encoding="utf-8"), marker
                )
                actual = score.render_human(
                    self.result, lang=lang, version=self.version
                ).rstrip("\n")
                self.assertEqual(
                    documented,
                    actual,
                    f"{readme} sample output is stale — regenerate it with "
                    f"`python3 score.py answers.example.csv --lang {lang}`",
                )


class TestEnglishReadmeHasNoStrayChinese(unittest.TestCase):
    """The English README's sample report must not carry Chinese labels.

    A translated README can keep Chinese in prose intentionally (e.g. naming the
    Chinese mirror), so this checks the sample REPORT block specifically — that
    is where a stale paste shows up.
    """

    def test_sample_block_is_pure_english(self) -> None:
        text = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")
        block = _first_fence_after(text, "Example output:")
        found = CJK.findall(block)
        self.assertEqual(
            found,
            [],
            "English README sample output contains Chinese characters "
            f"{sorted(set(found))} — it is a stale paste from the zh report",
        )


class TestLevelLabelsMatchDocs(unittest.TestCase):
    """Maturity-level labels in the docs must be the ones the tool prints.

    This exists because the English README once called L3 "Basically Compliant"
    in its band table while the tool printed "Basic" — on the same page as an
    example that showed "L3 Basic".
    """

    #: (doc file, the locale whose labels that doc must use)
    DOC_LOCALES = [
        ("README.md", "en"),
        ("SCORING.md", "en"),
        ("README.zh.md", "zh"),
        ("SCORING.zh.md", "zh"),
    ]

    def test_band_table_labels_match_tool(self) -> None:
        for doc, lang in self.DOC_LOCALES:
            path = _REPO_ROOT / doc
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            # Table rows that start with a level code, e.g. '| L3 Basic | 50% ...'
            for code, label in re.findall(r"^\|\s*(L[1-4])\s+([^|]+?)\s*\|", text, re.M):
                expected = score.LEVEL_LABELS[code][lang]
                with self.subTest(doc=doc, level=code):
                    self.assertEqual(
                        label,
                        expected,
                        f"{doc} calls {code} '{label}' but the tool prints "
                        f"'{expected}' — they must agree",
                    )


class TestVersionReferencesAgree(unittest.TestCase):
    """VERSION, the README badges, and CITATION.cff must state the same version."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.version = (_REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    def test_readme_badges_match_version_file(self) -> None:
        for readme in ("README.md", "README.zh.md"):
            with self.subTest(readme=readme):
                text = (_REPO_ROOT / readme).read_text(encoding="utf-8")
                badges = re.findall(r"questionnaire-v([0-9]+\.[0-9]+\.[0-9]+)", text)
                self.assertTrue(badges, f"{readme}: no questionnaire version badge")
                for badge_version in badges:
                    self.assertEqual(
                        badge_version,
                        self.version,
                        f"{readme} badge says v{badge_version} but VERSION is "
                        f"{self.version}",
                    )

    def test_citation_matches_version_file(self) -> None:
        text = (_REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
        # 'version:' at line start — NOT 'cff-version:', which is the file format.
        match = re.search(r"^version:\s*(\S+)", text, re.M)
        self.assertIsNotNone(match, "CITATION.cff has no version field")
        assert match is not None
        self.assertEqual(match.group(1), self.version)


if __name__ == "__main__":
    unittest.main()
