#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the AI-Ready Data scoring tool (stdlib unittest)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple
from unittest import mock

# Make ``scoring/`` importable whether this file is run directly, via
# ``unittest discover`` from the repo root, or as part of the ``test`` package.
_REPO_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("scoring", "scripts"):
    _p = str(_REPO_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import score


def _rows(*triples: Tuple[str, str, str]) -> List[Tuple[str, str, str]]:
    return list(triples)


def _full_dim(dim: str, answers: List[str]) -> List[Tuple[str, str, str]]:
    """Build (dim, qN, answer) rows for a dimension from a list of answers."""
    return [(dim, f"q{i + 1}", a) for i, a in enumerate(answers)]


class TestClassifyLevel(unittest.TestCase):
    def test_bands(self) -> None:
        self.assertEqual(score.classify_level(0.0)[0], "L1")
        self.assertEqual(score.classify_level(24.999)[0], "L1")
        # Boundary: exactly 25.0 -> L2 (falls in higher band).
        self.assertEqual(score.classify_level(25.0)[0], "L2")
        self.assertEqual(score.classify_level(49.999)[0], "L2")
        self.assertEqual(score.classify_level(50.0)[0], "L3")
        self.assertEqual(score.classify_level(74.999)[0], "L3")
        self.assertEqual(score.classify_level(75.0)[0], "L4")
        # Top band is closed: 100% -> L4.
        self.assertEqual(score.classify_level(100.0)[0], "L4")

    def test_labels(self) -> None:
        # Default (primary) labels are English; see LEVEL_LABELS for both locales.
        self.assertEqual(score.classify_level(10.0), ("L1", "Not Started"))
        self.assertEqual(score.classify_level(30.0), ("L2", "Initial Practice"))
        self.assertEqual(score.classify_level(60.0), ("L3", "Basic"))
        self.assertEqual(score.classify_level(90.0), ("L4", "Mature & Leading"))


class TestNormalizeAnswer(unittest.TestCase):
    def test_letters_case_insensitive(self) -> None:
        self.assertEqual(score.normalize_answer("a"), "A")
        self.assertEqual(score.normalize_answer(" d "), "D")

    def test_na_variants(self) -> None:
        for token in ("N/A", "n/a", "NA", "na", " NA "):
            self.assertEqual(score.normalize_answer(token), score.NA)

    def test_unknown_raises(self) -> None:
        with self.assertRaises(score.ValidationError):
            score.normalize_answer("Z")


class TestWorkedExample(unittest.TestCase):
    """Spec worked example: dim2 with 2A/2B/6C/2D/0NA => 22, 45.8% => L2."""

    def _dim2_rows(self) -> List[Tuple[str, str, str]]:
        answers = ["A", "A", "B", "B", "C", "C", "C", "C", "C", "C", "D", "D"]
        return _full_dim("dim2", answers)

    def test_dim2_score_and_rate(self) -> None:
        result = score.score_answers(self._dim2_rows())
        dim2 = next(d for d in result.dimensions if d.dimension == "dim2")
        # 2*0 + 2*1 + 6*2 + 2*4 = 0 + 2 + 12 + 8 = 22
        self.assertEqual(dim2.score, 22)
        self.assertEqual(dim2.n_answered, 12)
        self.assertEqual(dim2.n_na, 0)
        # 22 / (12*4) * 100 = 22/48*100 = 45.833...
        self.assertAlmostEqual(dim2.get_rate, 45.8333, places=3)
        self.assertEqual(round(dim2.get_rate, 1), 45.8)
        self.assertEqual(dim2.level_code, "L2")
        self.assertEqual(dim2.level_label, "Initial Practice")

    def test_dim2_d_ratio(self) -> None:
        result = score.score_answers(self._dim2_rows())
        dim2 = next(d for d in result.dimensions if d.dimension == "dim2")
        self.assertEqual(dim2.d_count, 2)
        # 2 D answers out of 12 answered = 0.1666...
        self.assertAlmostEqual(dim2.d_ratio, 2 / 12, places=6)


class TestNAExclusion(unittest.TestCase):
    def test_na_excluded_from_denominator(self) -> None:
        # dim1: 6 questions, 2 are N/A, remaining 4 = A,B,C,D
        rows = _full_dim("dim1", ["A", "B", "C", "D", "N/A", "N/A"])
        result = score.score_answers(rows)
        dim1 = next(d for d in result.dimensions if d.dimension == "dim1")
        self.assertEqual(dim1.n_answered, 4)
        self.assertEqual(dim1.n_na, 2)
        # score = 0+1+2+4 = 7; denom = 4*4 = 16 => 43.75%
        self.assertEqual(dim1.score, 7)
        self.assertAlmostEqual(dim1.get_rate, 43.75, places=4)
        self.assertTrue(dim1.applicable)

    def test_na_reduces_overall_denominator(self) -> None:
        # One answered A (score 0) + one N/A. Overall answered = 1, rate = 0.
        rows = [("dim1", "q1", "A"), ("dim1", "q2", "N/A")]
        result = score.score_answers(rows)
        self.assertEqual(result.overall.n_answered, 1)
        self.assertEqual(result.overall.total_score, 0)
        self.assertEqual(result.overall.get_rate, 0.0)


class TestAllNADimension(unittest.TestCase):
    def test_all_na_not_applicable(self) -> None:
        rows = _full_dim("dim5", ["N/A"] * 5)
        result = score.score_answers(rows)
        dim5 = next(d for d in result.dimensions if d.dimension == "dim5")
        self.assertFalse(dim5.applicable)
        self.assertIsNone(dim5.get_rate)
        self.assertIsNone(dim5.level_code)
        self.assertIsNone(dim5.d_ratio)
        self.assertEqual(dim5.n_answered, 0)
        self.assertEqual(dim5.n_na, 5)

    def test_all_na_excluded_from_overall(self) -> None:
        # dim1 answered with a single A; dim5 all N/A.
        rows = _full_dim("dim1", ["A"] * 6) + _full_dim("dim5", ["N/A"] * 5)
        result = score.score_answers(rows)
        # Only dim1's 6 answered questions count toward the overall denominator.
        self.assertEqual(result.overall.n_answered, 6)

    def test_everything_na_overall_not_applicable(self) -> None:
        rows = _full_dim("dim6", ["N/A"] * 5)
        result = score.score_answers(rows)
        self.assertEqual(result.overall.n_answered, 0)
        self.assertIsNone(result.overall.get_rate)
        self.assertIsNone(result.overall.level_code)


class TestDRatio(unittest.TestCase):
    def test_overall_d_ratio(self) -> None:
        # 3 D's, 1 A => 4 answered, D-ratio = 0.75
        rows = _full_dim("dim4", ["D", "D", "D", "A", "N/A"])
        result = score.score_answers(rows)
        dim4 = next(d for d in result.dimensions if d.dimension == "dim4")
        self.assertEqual(dim4.d_count, 3)
        self.assertEqual(dim4.n_answered, 4)
        self.assertAlmostEqual(dim4.d_ratio, 0.75, places=6)
        self.assertEqual(result.overall.d_count, 3)
        self.assertAlmostEqual(result.overall.d_ratio, 0.75, places=6)


class TestWeightedOverall(unittest.TestCase):
    def test_weighted_default_equals_unweighted_when_all_equal(self) -> None:
        rows = (
            _full_dim("dim1", ["C"] * 6)  # each 50%
            + _full_dim("dim2", ["A"] * 12)  # 0%
        )
        result = score.score_answers(rows, weights=[1, 1, 1, 1, 1, 1])
        # dim1 = 50%, dim2 = 0%; only these two applicable.
        # weighted = (50 + 0) / 2 = 25.0
        self.assertAlmostEqual(result.overall.weighted_get_rate, 25.0, places=4)

    def test_weighted_respects_weights(self) -> None:
        rows = (
            _full_dim("dim1", ["C"] * 6)  # 50%
            + _full_dim("dim2", ["A"] * 12)  # 0%
        )
        # Weight dim1 heavily.
        result = score.score_answers(rows, weights=[3, 1, 1, 1, 1, 1])
        # (3*50 + 1*0) / (3+1) = 150/4 = 37.5
        self.assertAlmostEqual(result.overall.weighted_get_rate, 37.5, places=4)


class TestStrictMode(unittest.TestCase):
    def test_unknown_answer_warns_by_default(self) -> None:
        rows = [("dim1", "q1", "Z")]
        result = score.score_answers(rows, strict=False)
        self.assertTrue(any("unknown answer" in w for w in result.warnings))

    def test_unknown_answer_raises_in_strict(self) -> None:
        rows = [("dim1", "q1", "Z")]
        with self.assertRaises(score.ValidationError):
            score.score_answers(rows, strict=True)

    def test_wrong_count_warns_by_default(self) -> None:
        rows = _full_dim("dim1", ["A"])  # only 1, expected 6
        result = score.score_answers(rows, strict=False)
        self.assertTrue(any("expected 6" in w for w in result.warnings))

    def test_wrong_count_raises_in_strict(self) -> None:
        rows = _full_dim("dim1", ["A"])
        with self.assertRaises(score.ValidationError):
            score.score_answers(rows, strict=True)


class TestLoaders(unittest.TestCase):
    def test_csv_roundtrip(self) -> None:
        content = "dimension,question,answer\ndim1,q1,A\ndim1,q2,na\n"
        with tempfile.NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            rows = score.load_answers(path)
            self.assertEqual(rows, [("dim1", "q1", "A"), ("dim1", "q2", "na")])
        finally:
            os.unlink(path)

    def test_json_nested(self) -> None:
        data = {"dim1": {"q1": "A", "q2": "B"}}
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump(data, fh)
            path = fh.name
        try:
            rows = score.load_answers(path)
            self.assertIn(("dim1", "q1", "A"), rows)
            self.assertIn(("dim1", "q2", "B"), rows)
        finally:
            os.unlink(path)

    def test_json_flat(self) -> None:
        data = [
            {"dimension": "dim1", "question": "q1", "answer": "A"},
            {"dimension": "dim1", "question": "q2", "answer": "B"},
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump(data, fh)
            path = fh.name
        try:
            rows = score.load_answers(path)
            self.assertEqual(
                rows, [("dim1", "q1", "A"), ("dim1", "q2", "B")]
            )
        finally:
            os.unlink(path)

    def test_bad_extension(self) -> None:
        with self.assertRaises(score.ValidationError):
            score.load_answers("answers.txt")


class TestHostileInputIsAValidationError(unittest.TestCase):
    """A malformed answers file must be a ValidationError, never a traceback.

    The answers file is the only untrusted input this tool takes (see
    SECURITY.md), and the documented contract is 'validation error: ...' with
    exit code 2. Each of these previously escaped as an uncaught exception.
    """

    def _write(self, content: bytes, suffix: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as fh:
            fh.write(content)
            self.addCleanup(os.unlink, fh.name)
            return fh.name

    def test_malformed_json(self) -> None:
        path = self._write(b"not json at all {", ".json")
        with self.assertRaises(score.ValidationError):
            score.load_answers(path)

    def test_deeply_nested_json(self) -> None:
        # json has no depth limit; 200k open brackets exhausts the C stack.
        path = self._write(b"[" * 200_000, ".json")
        with self.assertRaises(score.ValidationError):
            score.load_answers(path)

    def test_non_utf8_bytes(self) -> None:
        path = self._write(b"dimension,question,answer\n\xe0\xa0dim1,q1,A\n", ".csv")
        with self.assertRaises(score.ValidationError):
            score.load_answers(path)

    def test_directory_instead_of_file(self) -> None:
        with tempfile.TemporaryDirectory(suffix=".csv") as tmp:
            with self.assertRaises(score.ValidationError):
                score.load_answers(tmp)

    def test_missing_file_still_raises_filenotfound(self) -> None:
        # main() reports a missing file with its own clearer message, so this
        # one deliberately stays a FileNotFoundError.
        with self.assertRaises(FileNotFoundError):
            score.load_answers("definitely-not-here.csv")

    def test_cli_exits_2_rather_than_crashing(self) -> None:
        path = self._write(b"{ oops", ".json")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = score.main([path])
        self.assertEqual(code, 2)
        self.assertIn("validation error", stderr.getvalue())


class TestDisplayWidth(unittest.TestCase):
    """Table columns are measured in terminal columns, not in characters."""

    def test_cjk_counts_as_two_columns(self) -> None:
        self.assertEqual(score._display_width("abc"), 3)
        self.assertEqual(score._display_width("维度"), 4)
        self.assertEqual(score._display_width("dim1 成本与业务价值"), 5 + 14)

    def test_zh_table_rows_are_aligned(self) -> None:
        rows = _full_dim("dim1", ["C"] * 6)
        rendered = score.render_human(score.score_answers(rows), lang="zh")
        table = [
            line for line in rendered.splitlines()
            if line.startswith(("+", "|"))
        ]
        self.assertTrue(table)
        widths = {score._display_width(line) for line in table}
        self.assertEqual(
            len(widths),
            1,
            f"ragged Chinese table -- row widths were {sorted(widths)}",
        )

    def test_bilingual_table_rows_are_aligned(self) -> None:
        rows = _full_dim("dim1", ["C"] * 6)
        rendered = score.render_human(score.score_answers(rows), lang="both")
        table = [
            line for line in rendered.splitlines()
            if line.startswith(("+", "|"))
        ]
        widths = {score._display_width(line) for line in table}
        self.assertEqual(len(widths), 1, f"row widths were {sorted(widths)}")


class TestDuplicateDeduplication(unittest.TestCase):
    """A repeated question id must not be scored twice."""

    def test_duplicate_does_not_inflate_dimension(self) -> None:
        # Six C answers = 12 points over 6 questions. Repeating q1 as a D must
        # replace it, not append a seventh scored answer.
        rows = _full_dim("dim1", ["C"] * 6)
        rows.append(("dim1", "q1", "D"))
        dim1 = score.score_answers(rows).dimensions[0]
        self.assertEqual(dim1.n_answered, 6)
        self.assertEqual(dim1.score, 14)  # q1 became D (4) instead of C (2)
        self.assertEqual(dim1.d_count, 1)

    def test_last_occurrence_wins_case_insensitively(self) -> None:
        rows = _full_dim("dim1", ["A"] * 6)
        rows.append(("dim1", "Q1", "D"))  # same id, different case
        dim1 = score.score_answers(rows).dimensions[0]
        self.assertEqual(dim1.n_answered, 6)
        self.assertEqual(dim1.score, 4)

    def test_duplicate_na_replaces_a_scored_answer(self) -> None:
        rows = _full_dim("dim1", ["D"] * 6)
        rows.append(("dim1", "q1", "N/A"))
        dim1 = score.score_answers(rows).dimensions[0]
        self.assertEqual(dim1.n_answered, 5)
        self.assertEqual(dim1.n_na, 1)
        self.assertEqual(dim1.score, 20)


class TestExampleFixturesAgree(unittest.TestCase):
    """The CSV and JSON example fixtures must produce identical results."""

    def setUp(self) -> None:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.here = os.path.join(repo_root, "scoring")

    def test_csv_and_json_match(self) -> None:
        csv_path = os.path.join(self.here, "answers.example.csv")
        json_path = os.path.join(self.here, "answers.example.json")
        if not (os.path.exists(csv_path) and os.path.exists(json_path)):
            self.skipTest("example fixtures not present")
        csv_res = score.result_to_dict(
            score.score_answers(score.load_answers(csv_path))
        )
        json_res = score.result_to_dict(
            score.score_answers(score.load_answers(json_path))
        )
        self.assertEqual(csv_res, json_res)

    def test_example_dim2_matches_spec(self) -> None:
        csv_path = os.path.join(self.here, "answers.example.csv")
        if not os.path.exists(csv_path):
            self.skipTest("example CSV not present")
        result = score.score_answers(score.load_answers(csv_path))
        dim2 = next(d for d in result.dimensions if d.dimension == "dim2")
        self.assertEqual(dim2.score, 22)
        self.assertEqual(round(dim2.get_rate, 1), 45.8)
        self.assertEqual(dim2.level_code, "L2")
        # dim5 is all N/A in the fixture.
        dim5 = next(d for d in result.dimensions if d.dimension == "dim5")
        self.assertFalse(dim5.applicable)


class TestBilingualOutput(unittest.TestCase):
    """Bilingual (zh / en / both) report rendering."""

    def _result(self):
        rows = [("dim1", f"Q{i}", "C") for i in range(1, 7)]
        rows += [("dim2", f"Q{i}", "D") for i in range(1, 13)]
        rows += [("dim3", f"Q{i}", "A") for i in range(1, 13)]
        rows += [("dim4", f"Q{i}", "B") for i in range(1, 6)]
        rows += [("dim5", f"Q{i}", "N/A") for i in range(1, 6)]
        rows += [("dim6", f"Q{i}", "C") for i in range(1, 6)]
        return score.score_answers(rows)

    def test_level_label_locales(self):
        self.assertEqual(score.level_label("L1", "zh"), "未起步")
        self.assertEqual(score.level_label("L1", "en"), "Not Started")
        self.assertEqual(score.level_label("L4", "en"), "Mature & Leading")
        self.assertEqual(score.level_label("L2", "both"), "Initial Practice / 初步实践")
        self.assertIsNone(score.level_label(None, "en"))

    def test_dimension_name_locales(self):
        self.assertEqual(score.dimension_name("dim1", "zh"), "成本与业务价值")
        self.assertEqual(score.dimension_name("dim6", "en"), "Security & Compliance")
        self.assertIn("/", score.dimension_name("dim3", "both"))

    def test_render_en_has_no_chinese_labels(self):
        out = score.render_human(self._result(), lang="en")
        self.assertIn("Dimension", out)
        self.assertIn("Not Started", out)
        self.assertIn("not applicable", out)
        for zh in ("维度", "未起步", "初步实践", "成熟度层级", "暂不适用"):
            self.assertNotIn(zh, out)

    def test_render_zh_has_chinese_labels(self):
        out = score.render_human(self._result(), lang="zh")
        self.assertIn("维度", out)
        self.assertIn("暂不适用", out)
        self.assertNotIn("Dimension", out)

    def test_render_both_is_bilingual(self):
        out = score.render_human(self._result(), lang="both")
        self.assertIn("Dimension / 维度", out)
        self.assertIn("Level / 成熟度层级", out)

    def test_json_carries_both_locales(self):
        payload = score.result_to_dict(self._result())
        dim1 = payload["dimensions"][0]
        self.assertEqual(dim1["dimension_name_zh"], "成本与业务价值")
        self.assertEqual(dim1["dimension_name_en"], "Cost & Business Value")
        self.assertIsNotNone(dim1["level_label_en"])
        # all-N/A dimension carries both not-applicable labels
        dim5 = next(d for d in payload["dimensions"] if d["dimension"] == "dim5")
        self.assertFalse(dim5["applicable"])
        self.assertEqual(dim5["not_applicable_label_en"], "not applicable")
        self.assertEqual(dim5["not_applicable_label_zh"], "暂不适用")
        self.assertIsNotNone(payload["overall"]["level_label_en"])

    def test_cli_lang_flag_accepted(self):
        parser = score.build_parser()
        for lang in ("zh", "en", "both"):
            args = parser.parse_args(["answers.example.csv", "--lang", lang])
            self.assertEqual(args.lang, lang)
        # default is English (primary locale)
        self.assertEqual(parser.parse_args(["answers.example.csv"]).lang, "en")



class TestRobustness(unittest.TestCase):
    """Hardening against mis-authored input and float-boundary error."""

    def test_duplicate_question_id_is_reported(self) -> None:
        rows = _full_dim("dim1", ["C"] * 6)
        rows.append(("dim1", "q1", "D"))  # duplicate of q1
        result = score.score_answers(rows)
        self.assertTrue(
            any("duplicate question id" in w for w in result.warnings),
            msg=f"warnings were: {result.warnings}",
        )

    def test_duplicate_question_id_is_fatal_under_strict(self) -> None:
        rows = _full_dim("dim1", ["C"] * 6)
        rows.append(("dim1", "Q1", "D"))  # same id, different case
        with self.assertRaises(score.ValidationError):
            score.score_answers(rows, strict=True)

    def test_boundary_survives_float_error(self) -> None:
        # A rate that is mathematically exactly on a band boundary must land in
        # the higher band even when float division nudges it below.
        self.assertEqual(score.classify_level(24.999999999999996)[0], "L2")
        self.assertEqual(score.classify_level(49.99999999999999)[0], "L3")
        self.assertEqual(score.classify_level(75.00000000000001)[0], "L4")

    def test_genuinely_below_boundary_stays_lower(self) -> None:
        # Rounding must not swallow a real gap: 24.99 is genuinely below 25.
        self.assertEqual(score.classify_level(24.99)[0], "L1")
        self.assertEqual(score.classify_level(49.9)[0], "L2")


class TestQuestionIdValidation(unittest.TestCase):
    """A question id must name a question that exists in that dimension.

    Without this, a typo such as 'q77' in the 6-question dim1 was scored
    silently as long as the dimension's row count happened to come out right.
    """

    def test_out_of_range_id_is_reported(self) -> None:
        rows = _full_dim("dim1", ["C"] * 6)
        rows[2] = ("dim1", "q77", "C")  # dim1 only has Q1..Q6
        result = score.score_answers(rows)
        self.assertTrue(
            any("out of range" in w for w in result.warnings),
            msg=f"warnings were: {result.warnings}",
        )

    def test_out_of_range_id_is_fatal_under_strict(self) -> None:
        rows = _full_dim("dim1", ["C"] * 6)
        rows[2] = ("dim1", "q77", "C")
        with self.assertRaises(score.ValidationError):
            score.score_answers(rows, strict=True)

    def test_malformed_id_is_reported(self) -> None:
        rows = _full_dim("dim2", ["C"] * 12)
        rows[0] = ("dim2", "first-question", "C")
        result = score.score_answers(rows)
        self.assertTrue(
            any("malformed question id" in w for w in result.warnings),
            msg=f"warnings were: {result.warnings}",
        )

    def test_boundary_ids_are_accepted(self) -> None:
        # Q1 and QN (the last question) must both validate cleanly.
        for dim, count in score.DIMENSION_QUESTION_COUNTS.items():
            with self.subTest(dim=dim):
                rows = _full_dim(dim, ["C"] * count)
                result = score.score_answers(rows)
                self.assertEqual(
                    [w for w in result.warnings if dim in w and "id" in w], []
                )

    def test_id_case_does_not_matter(self) -> None:
        upper = score.score_answers([("dim4", f"Q{i}", "C") for i in range(1, 6)])
        lower = score.score_answers([("dim4", f"q{i}", "C") for i in range(1, 6)])
        # Only dim4 was supplied, so the other dimensions warn about their
        # counts; what matters is that neither casing draws an id complaint.
        for label, result in (("upper", upper), ("lower", lower)):
            with self.subTest(casing=label):
                self.assertEqual(
                    [w for w in result.warnings if "dim4" in w], []
                )
        self.assertEqual(upper.overall.total_score, lower.overall.total_score)


class TestWeightValidation(unittest.TestCase):
    """--weights must be non-negative and not all zero."""

    def test_negative_weight_rejected(self) -> None:
        with self.assertRaises(score.ValidationError):
            score.parse_weights("-1,1,1,1,1,1")

    def test_all_zero_weights_rejected(self) -> None:
        with self.assertRaises(score.ValidationError):
            score.parse_weights("0,0,0,0,0,0")

    def test_wrong_count_rejected(self) -> None:
        with self.assertRaises(score.ValidationError):
            score.parse_weights("1,1,1")

    def test_partial_zero_weights_allowed(self) -> None:
        # Zeroing out individual dimensions is legitimate (e.g. "ignore dim5").
        self.assertEqual(
            score.parse_weights("1,1,1,1,0,0"), [1.0, 1.0, 1.0, 1.0, 0.0, 0.0]
        )

    def test_no_weightable_dimension_warns(self) -> None:
        # Weight only dim5, then make dim5 entirely N/A: nothing to weight by.
        rows = _full_dim("dim5", ["N/A"] * 5)
        result = score.score_answers(rows, weights=[0, 0, 0, 0, 1, 0])
        self.assertIsNone(result.overall.weighted_get_rate)
        self.assertTrue(
            any("no weighted overall" in w for w in result.warnings),
            msg=f"warnings were: {result.warnings}",
        )


class TestQuestionnaireVersionStamp(unittest.TestCase):
    """Reports must carry the questionnaire version they were produced against.

    Scores are only comparable within one version of the question bank, so an
    archived report that does not name its version cannot be interpreted later.
    """

    def setUp(self) -> None:
        self.result = score.score_answers(_full_dim("dim1", ["C"] * 6))

    def test_reads_version_from_repo(self) -> None:
        expected = (_REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(score.read_questionnaire_version(), expected)

    def test_human_report_stamps_version(self) -> None:
        text = score.render_human(self.result, lang="en", version="9.9.9")
        self.assertIn("questionnaire: v9.9.9", text)

    def test_human_report_stamps_version_zh(self) -> None:
        text = score.render_human(self.result, lang="zh", version="9.9.9")
        self.assertIn("问卷版本: v9.9.9", text)

    def test_version_omitted_when_unknown(self) -> None:
        # score.py stays usable as a standalone copy with no VERSION alongside.
        text = score.render_human(self.result, lang="en", version=None)
        self.assertNotIn("questionnaire:", text)

    def test_json_carries_version(self) -> None:
        payload = score.result_to_dict(self.result, version="9.9.9")
        self.assertEqual(payload["questionnaire_version"], "9.9.9")

    def test_json_version_key_always_present(self) -> None:
        # Downstream consumers can rely on the key existing, even if it is null.
        payload = score.result_to_dict(self.result)
        self.assertIn("questionnaire_version", payload)
        self.assertIsNone(payload["questionnaire_version"])

    def test_unrelated_version_file_is_not_stamped_as_ours(self) -> None:
        """A VERSION file that is not MAJOR.MINOR.PATCH must read as unknown.

        Copied out of the repository, score.py resolves _REPO_ROOT to whatever
        directory sits above it. An unrelated VERSION file there (a Node
        project's 'v18', a checked-out tag name) must not be stamped onto a
        report as if it were the questionnaire's.
        """
        for content in ("v18", "1.0", "not a version", "", "1.0.0-rc1"):
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as tmp:
                    (Path(tmp) / "VERSION").write_text(content, encoding="utf-8")
                    with mock.patch.object(score, "_REPO_ROOT", Path(tmp)):
                        self.assertIsNone(score.read_questionnaire_version())

    def test_well_formed_version_file_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "VERSION").write_text("2.3.4\n", encoding="utf-8")
            with mock.patch.object(score, "_REPO_ROOT", Path(tmp)):
                self.assertEqual(score.read_questionnaire_version(), "2.3.4")


if __name__ == "__main__":
    unittest.main()
