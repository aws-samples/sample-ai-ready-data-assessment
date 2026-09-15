#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""AI-Ready Data self-assessment scoring / grading tool.

Implements the authoritative scoring spec:

- 45 questions across 6 dimensions.
  Question counts: dim1=6, dim2=12, dim3=12, dim4=5, dim5=5, dim6=5.
- Per-question option scores: A=0, B=1, C=2, D=4.
- N/A answers are NOT scored AND are excluded from that dimension's denominator.
- Dimension score      = sum of answered (non-N/A) question scores.
- Dimension get-rate   = dim_score / (n_answered_in_dim * 4) * 100%.
- A dimension where ALL questions are N/A is EXCLUDED from radar/comparison
  and reported as '暂不适用 (not applicable)', NOT 0%.
- Total score          = sum of all dimension scores.
- Overall get-rate     = total_score / (sum_d n_answered_d * 4) * 100%.
- Optional weighted overall (default OFF): sum(w_d * dim_get_rate_d) / sum(w_d).
- Maturity levels by get-rate, half-open intervals [lo, hi); top bucket
  L4 includes 100%. A boundary value such as exactly 25.0% falls in L2.
      L1 Not Started / 未起步        : [0, 25)
      L2 Initial Practice / 初步实践 : [25, 50)
      L3 Basic / 基本达标            : [50, 75)
      L4 Mature & Leading / 成熟领先 : [75, 100]
- D-ratio = count(D answers) / n_answered (overall and per-dimension).

Answer files are validated on three axes: the dimension id must be known, the
question id must be a ``Q<n>`` within that dimension's range, and each dimension
must carry exactly its expected number of rows. Problems are warnings by
default and fatal under ``--strict``.

A question id repeated within one dimension is deduplicated — the last row wins
and a warning is raised — so a copy-paste slip cannot silently inflate a
dimension by scoring the same question twice.

Every report carries the questionnaire version it was produced against, because
scores are only comparable within one version of the question bank.

Reports default to **English** (``--lang en``); use ``--lang zh`` for Chinese or
``--lang both`` for a bilingual "English / 中文" table. JSON output always
carries both locales (``*_zh`` / ``*_en`` labels).

Standard library only. Run as:  python3 score.py <answers-file>
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#: Number of questions expected in each dimension (dimension id -> count).
DIMENSION_QUESTION_COUNTS: Dict[str, int] = {
    "dim1": 6,
    "dim2": 12,
    "dim3": 12,
    "dim4": 5,
    "dim5": 5,
    "dim6": 5,
}

#: Ordered dimension ids (stable output order).
DIMENSION_ORDER: List[str] = list(DIMENSION_QUESTION_COUNTS.keys())

#: Score awarded per option letter.
OPTION_SCORES: Dict[str, int] = {"A": 0, "B": 1, "C": 2, "D": 4}

#: Sentinel string for "not applicable" answers (normalized form).
NA = "N/A"

#: Maturity level bands as (lo, hi, code, label). Half-open [lo, hi) except the
#: final band which is closed [lo, hi] so that exactly 100% -> L4.
#: The label here is the English (default/primary) label; see LEVEL_LABELS for
#: both locales.
LEVEL_BANDS: List[Tuple[float, float, str, str]] = [
    (0.0, 25.0, "L1", "Not Started"),
    (25.0, 50.0, "L2", "Initial Practice"),
    (50.0, 75.0, "L3", "Basic"),
    (75.0, 100.0, "L4", "Mature & Leading"),
]

#: Maturity level labels per locale (level code -> {lang -> label}).
LEVEL_LABELS: Dict[str, Dict[str, str]] = {
    "L1": {"zh": "未起步", "en": "Not Started"},
    "L2": {"zh": "初步实践", "en": "Initial Practice"},
    "L3": {"zh": "基本达标", "en": "Basic"},
    "L4": {"zh": "成熟领先", "en": "Mature & Leading"},
}

#: Human-readable dimension names per locale.
DIMENSION_NAMES: Dict[str, Dict[str, str]] = {
    "dim1": {"zh": "成本与业务价值", "en": "Cost & Business Value"},
    "dim2": {"zh": "数据基础与质量", "en": "Data Foundation & Quality"},
    "dim3": {"zh": "平台架构与运维", "en": "Platform Architecture & Operations"},
    "dim4": {"zh": "组织与人才", "en": "Organization & Talent"},
    "dim5": {"zh": "治理与信任", "en": "Governance & Trust"},
    "dim6": {"zh": "安全与合规", "en": "Security & Compliance"},
}

#: Label used for a dimension where every question is N/A.
NOT_APPLICABLE_LABEL = "not applicable (暂不适用)"

#: Per-locale "not applicable" label.
NOT_APPLICABLE_LABELS: Dict[str, str] = {
    "zh": "暂不适用",
    "en": "not applicable",
}

#: Supported output languages. 'en' is the default; 'both' renders bilingual.
LANG_CHOICES = ("en", "zh", "both")

#: Accepted shape of a question id, e.g. 'Q1' / 'q12' (matched case-insensitively).
QUESTION_ID_RE = re.compile(r"Q(\d+)\Z", re.IGNORECASE)

#: Repository root relative to this file, used to locate the VERSION file.
_REPO_ROOT = Path(__file__).resolve().parent.parent

#: Shape of a questionnaire version: MAJOR.MINOR.PATCH.
_VERSION_RE = re.compile(r"\d+\.\d+\.\d+\Z")


def read_questionnaire_version() -> Optional[str]:
    """Return the questionnaire version from the repo ``VERSION`` file.

    Returns ``None`` when the file is absent — ``score.py`` stays usable as a
    standalone script copied out of the repository, it just cannot stamp a
    version onto the report in that case.

    The contents must look like ``MAJOR.MINOR.PATCH``. Copied out of the
    repository this script resolves ``_REPO_ROOT`` to whatever directory happens
    to sit above it, and an unrelated ``VERSION`` file there must not be stamped
    onto a report as if it were the questionnaire's.
    """
    try:
        version = (_REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return version if _VERSION_RE.match(version) else None

#: UI strings per locale, used by the human-readable renderer.
UI_STRINGS: Dict[str, Dict[str, str]] = {
    "zh": {
        "title": "AI-Ready Data — 自检结果",
        "h_dimension": "维度",
        "h_score": "得分",
        "h_answered": "作答数",
        "h_get_rate": "得分率",
        "h_level": "成熟度层级",
        "h_d_ratio": "D档占比",
        "overall": "总体",
        "total_score": "总分",
        "answered": "作答数",
        "get_rate": "得分率",
        "level": "层级",
        "d_ratio": "D档占比",
        "no_answers": "总体：没有可计分的作答。",
        "weighted": "加权总体",
        "warnings": "警告：",
        "questionnaire": "问卷版本",
    },
    "en": {
        "title": "AI-Ready Data — Self-Assessment Result",
        "h_dimension": "Dimension",
        "h_score": "Score",
        "h_answered": "Answered",
        "h_get_rate": "Get-rate",
        "h_level": "Level",
        "h_d_ratio": "D-ratio",
        "overall": "Overall",
        "total_score": "total_score",
        "answered": "answered",
        "get_rate": "get-rate",
        "level": "level",
        "d_ratio": "D-ratio",
        "no_answers": "Overall: no applicable answers.",
        "weighted": "Weighted overall",
        "warnings": "Warnings:",
        "questionnaire": "questionnaire",
    },
}


def level_label(code: Optional[str], lang: str) -> Optional[str]:
    """Return the maturity level label for ``code`` in ``lang``.

    For ``lang='both'`` a bilingual "English / 中文" label is returned.
    """
    if code is None:
        return None
    labels = LEVEL_LABELS.get(code)
    if labels is None:
        return code
    if lang == "both":
        return f"{labels['en']} / {labels['zh']}"
    return labels.get(lang, labels["en"])


def dimension_name(dim: str, lang: str) -> str:
    """Return the display name for a dimension id in ``lang``."""
    names = DIMENSION_NAMES.get(dim)
    if names is None:
        return dim
    if lang == "both":
        return f"{names['en']} / {names['zh']}"
    return names.get(lang, names["en"])


def not_applicable_label(lang: str) -> str:
    """Return the not-applicable label in ``lang``."""
    if lang == "both":
        return NOT_APPLICABLE_LABEL
    return NOT_APPLICABLE_LABELS.get(lang, NOT_APPLICABLE_LABELS["en"])


def ui(lang: str, key: str) -> str:
    """Return a UI string for ``key``; bilingual when ``lang='both'``."""
    if lang == "both":
        zh = UI_STRINGS["zh"][key]
        en = UI_STRINGS["en"][key]
        return en if zh == en else f"{en} / {zh}"
    return UI_STRINGS.get(lang, UI_STRINGS["en"])[key]


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #

class ValidationError(Exception):
    """Raised for a validation problem that is fatal under --strict."""


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

@dataclass
class Answer:
    """A single answered question."""

    dimension: str
    question: str
    answer: str  # normalized: one of A/B/C/D or 'N/A'


@dataclass
class DimensionResult:
    """Computed result for one dimension."""

    dimension: str
    score: int
    n_answered: int
    n_na: int
    applicable: bool
    get_rate: Optional[float]  # percent, or None when not applicable
    level_code: Optional[str]
    level_label: Optional[str]
    d_count: int
    d_ratio: Optional[float]  # fraction 0..1, or None when nothing answered


@dataclass
class OverallResult:
    """Computed overall / aggregate result."""

    total_score: int
    n_answered: int
    get_rate: Optional[float]
    level_code: Optional[str]
    level_label: Optional[str]
    d_count: int
    d_ratio: Optional[float]
    weighted_get_rate: Optional[float] = None
    weighted_level_code: Optional[str] = None
    weighted_level_label: Optional[str] = None


@dataclass
class ScoreResult:
    """Full scoring result: per-dimension + overall + collected warnings."""

    dimensions: List[DimensionResult]
    overall: OverallResult
    warnings: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Normalization / parsing helpers
# --------------------------------------------------------------------------- #

def normalize_answer(raw: str) -> str:
    """Normalize a raw answer token to A/B/C/D or 'N/A'.

    Accepts case-insensitive letters, and 'N/A', 'NA', 'na' for not-applicable.
    Raises ValidationError for anything else.
    """
    token = raw.strip().upper()
    if token in OPTION_SCORES:
        return token
    if token in {"N/A", "NA"}:
        return NA
    raise ValidationError(f"unknown answer letter: {raw!r}")


def _detect_format(path: str) -> str:
    """Return 'json' or 'csv' based on the file extension."""
    lower = path.lower()
    if lower.endswith(".json"):
        return "json"
    if lower.endswith(".csv"):
        return "csv"
    raise ValidationError(
        f"cannot detect format from extension: {path!r} (expected .csv or .json)"
    )


def load_answers(path: str) -> List[Tuple[str, str, str]]:
    """Load raw (dimension, question, answer) triples from a CSV or JSON file.

    The answer field is returned un-normalized; normalization happens later so
    that validation warnings/errors carry the original token.
    """
    fmt = _detect_format(path)
    if fmt == "csv":
        return _load_csv(path)
    return _load_json(path)


def _read_text(path: str, encoding: str) -> str:
    """Read an answers file as text, or raise ValidationError.

    The answers file is the only untrusted input this tool takes, so every way
    reading it can fail is funnelled into ValidationError — the CLI reports that
    as ``validation error: ...`` and exits 2. Without this a hostile or merely
    mistaken file (a binary blob renamed to ``.csv``, a directory, an unreadable
    path) escaped as an uncaught UnicodeDecodeError / OSError traceback.

    FileNotFoundError is deliberately re-raised: ``main`` reports a missing file
    on its own, and its message is clearer than a generic validation error.
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except FileNotFoundError:
        raise
    except IsADirectoryError as exc:
        raise ValidationError(f"{path} is a directory, not an answers file") from exc
    except UnicodeDecodeError as exc:
        raise ValidationError(
            f"{path} is not valid UTF-8 text -- an answers file is a UTF-8 "
            f"encoded CSV or JSON document ({exc})"
        ) from exc
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc


def _load_csv(path: str) -> List[Tuple[str, str, str]]:
    """Parse a CSV with header columns: dimension,question,answer."""
    text = _read_text(path, "utf-8-sig")
    rows: List[Tuple[str, str, str]] = []
    # newline="" so the csv module does its own line splitting, exactly as it
    # requires of a file handle.
    reader = csv.DictReader(io.StringIO(text, newline=""))
    try:
        fieldnames = reader.fieldnames
    except csv.Error as exc:
        raise ValidationError(f"{path} is not parsable as CSV: {exc}") from exc
    if fieldnames is None:
        raise ValidationError("CSV file is empty")
    cols = {name.strip().lower(): name for name in fieldnames}
    for required in ("dimension", "question", "answer"):
        if required not in cols:
            raise ValidationError(
                f"CSV missing required column {required!r}; "
                f"found {list(fieldnames)}"
            )
    try:
        for line in reader:
            dim = (line.get(cols["dimension"]) or "").strip()
            qid = (line.get(cols["question"]) or "").strip()
            ans = (line.get(cols["answer"]) or "").strip()
            if not dim and not qid and not ans:
                continue  # skip fully blank rows
            rows.append((dim, qid, ans))
    except csv.Error as exc:
        raise ValidationError(f"{path} is not parsable as CSV: {exc}") from exc
    return rows


def _load_json(path: str) -> List[Tuple[str, str, str]]:
    """Parse either the nested-object or flat-list JSON shape.

    Nested object:  {"dim1": {"q1": "A", "q2": "B"}, ...}
    Flat list:      [{"dimension": "dim1", "question": "q1", "answer": "A"}, ...]
    """
    text = _read_text(path, "utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path} is not valid JSON: {exc}") from exc
    except RecursionError as exc:
        # json has no depth limit, so a file of 200k '[' characters exhausts the
        # C stack. An answers file is at most two levels deep.
        raise ValidationError(
            f"{path} nests too deeply to parse -- an answers file is a flat "
            "list, or an object of dimension -> question -> answer"
        ) from exc

    rows: List[Tuple[str, str, str]] = []
    if isinstance(data, dict):
        for dim, questions in data.items():
            if not isinstance(questions, dict):
                raise ValidationError(
                    f"nested JSON: value for {dim!r} must be an object "
                    f"of question->answer, got {type(questions).__name__}"
                )
            for qid, ans in questions.items():
                rows.append((str(dim).strip(), str(qid).strip(), str(ans).strip()))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValidationError(
                    f"flat JSON: item {i} must be an object, "
                    f"got {type(item).__name__}"
                )
            try:
                dim = str(item["dimension"]).strip()
                qid = str(item["question"]).strip()
                ans = str(item["answer"]).strip()
            except KeyError as exc:
                raise ValidationError(
                    f"flat JSON: item {i} missing key {exc}"
                ) from exc
            rows.append((dim, qid, ans))
    else:
        raise ValidationError(
            "JSON root must be an object (nested) or a list (flat), "
            f"got {type(data).__name__}"
        )
    return rows


# --------------------------------------------------------------------------- #
# Level classification
# --------------------------------------------------------------------------- #

def classify_level(get_rate: float) -> Tuple[str, str]:
    """Map a get-rate percent to a maturity (code, label).

    Half-open bands [lo, hi); the top band L4 is closed so 100% -> L4.
    A value exactly on a boundary (e.g. 25.0) falls into the higher band.

    The rate is rounded to 9 decimal places first: a rate that is mathematically
    exactly on a boundary can arrive as 24.999999999999996 through float
    division (11/44*100 and 55.0 both exhibit this), which would otherwise be
    classified into the lower band and contradict the documented rule.
    """
    get_rate = round(get_rate, 9)
    for lo, hi, code, label in LEVEL_BANDS:
        is_last = code == LEVEL_BANDS[-1][2]
        if lo <= get_rate < hi or (is_last and get_rate == hi):
            return code, label
    # get_rate outside [0, 100]; clamp to nearest band for robustness.
    if get_rate < 0:
        return LEVEL_BANDS[0][2], LEVEL_BANDS[0][3]
    return LEVEL_BANDS[-1][2], LEVEL_BANDS[-1][3]


# --------------------------------------------------------------------------- #
# Core scoring
# --------------------------------------------------------------------------- #

def score_answers(
    raw_rows: List[Tuple[str, str, str]],
    weights: Optional[List[float]] = None,
    strict: bool = False,
) -> ScoreResult:
    """Compute the full scoring result from raw (dimension, question, answer) rows.

    :param raw_rows: un-normalized triples as loaded from a file.
    :param weights: optional 6 weights (w1..w6) enabling the weighted overall.
    :param strict: when True, validation problems raise ValidationError;
                   otherwise they are collected as warnings.
    :returns: a fully populated :class:`ScoreResult`.
    """
    warnings: List[str] = []

    def note(msg: str) -> None:
        if strict:
            raise ValidationError(msg)
        warnings.append(msg)

    # Group normalized answers by dimension, keyed by normalized question id so
    # that a repeated row replaces the earlier answer instead of being scored a
    # second time. dict preserves the first insertion position, so output order
    # still follows the file.
    by_dim: Dict[str, Dict[str, Answer]] = {d: {} for d in DIMENSION_ORDER}
    for dim, qid, raw_ans in raw_rows:
        if dim not in DIMENSION_QUESTION_COUNTS:
            note(f"unknown dimension {dim!r} (question {qid!r}) -- ignored")
            continue
        try:
            ans = normalize_answer(raw_ans)
        except ValidationError as exc:
            note(f"{dim}/{qid}: {exc}")
            continue
        # The question id must be a Q<n> that actually exists in this dimension.
        # Without this, a typo such as 'q77' in a 6-question dimension would be
        # scored silently as long as the row count happened to come out right.
        expected_n = DIMENSION_QUESTION_COUNTS[dim]
        id_match = QUESTION_ID_RE.match(qid.strip())
        if id_match is None:
            note(f"{dim}/{qid}: malformed question id -- expected 'Q<n>', e.g. 'Q1'")
        elif not 1 <= int(id_match.group(1)) <= expected_n:
            note(
                f"{dim}/{qid}: question id out of range -- {dim} has "
                f"{expected_n} questions (Q1..Q{expected_n})"
            )
        key = qid.upper()
        previous = by_dim[dim].get(key)
        if previous is not None:
            note(
                f"{dim}/{qid}: duplicate question id -- the last occurrence "
                f"wins, discarding the earlier answer {previous.answer!r}; "
                f"a question must appear exactly once"
            )
        by_dim[dim][key] = Answer(dimension=dim, question=qid, answer=ans)

    # Validate per-dimension question counts.
    for dim in DIMENSION_ORDER:
        got = len(by_dim[dim])
        expected = DIMENSION_QUESTION_COUNTS[dim]
        if got != expected:
            note(
                f"dimension {dim} has {got} questions, expected {expected}"
            )

    dim_results: List[DimensionResult] = []
    total_score = 0
    total_answered = 0
    total_d = 0

    for dim in DIMENSION_ORDER:
        answers = list(by_dim[dim].values())
        scored = [a for a in answers if a.answer != NA]
        n_answered = len(scored)
        n_na = len(answers) - n_answered
        d_count = sum(1 for a in scored if a.answer == "D")
        score = sum(OPTION_SCORES[a.answer] for a in scored)

        applicable = n_answered > 0
        if applicable:
            get_rate = score / (n_answered * 4) * 100.0
            level_code, level_label = classify_level(get_rate)
            d_ratio: Optional[float] = d_count / n_answered
        else:
            get_rate = None
            level_code = level_label = None
            d_ratio = None

        dim_results.append(
            DimensionResult(
                dimension=dim,
                score=score,
                n_answered=n_answered,
                n_na=n_na,
                applicable=applicable,
                get_rate=get_rate,
                level_code=level_code,
                level_label=level_label,
                d_count=d_count,
                d_ratio=d_ratio,
            )
        )

        if applicable:
            total_score += score
            total_answered += n_answered
            total_d += d_count

    # Overall.
    if total_answered > 0:
        overall_rate: Optional[float] = total_score / (total_answered * 4) * 100.0
        o_code, o_label = classify_level(overall_rate)
        overall_d_ratio: Optional[float] = total_d / total_answered
    else:
        overall_rate = None
        o_code = o_label = None
        overall_d_ratio = None

    overall = OverallResult(
        total_score=total_score,
        n_answered=total_answered,
        get_rate=overall_rate,
        level_code=o_code,
        level_label=o_label,
        d_count=total_d,
        d_ratio=overall_d_ratio,
    )

    # Optional weighted overall.
    if weights is not None:
        if len(weights) != len(DIMENSION_ORDER):
            raise ValidationError(
                f"--weights needs {len(DIMENSION_ORDER)} values, got {len(weights)}"
            )
        num = 0.0
        den = 0.0
        for w, res in zip(weights, dim_results):
            if res.applicable and res.get_rate is not None:
                num += w * res.get_rate
                den += w
        if den > 0:
            weighted = num / den
            wc, wl = classify_level(weighted)
            overall.weighted_get_rate = weighted
            overall.weighted_level_code = wc
            overall.weighted_level_label = wl
        else:
            note(
                "--weights was given but no weighted overall could be computed: "
                "every dimension carrying a non-zero weight is entirely N/A"
            )

    return ScoreResult(dimensions=dim_results, overall=overall, warnings=warnings)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def _fmt_pct(value: Optional[float]) -> str:
    return f"{value:.1f}%" if value is not None else "—"


def _fmt_ratio(value: Optional[float]) -> str:
    return f"{value * 100:.1f}%" if value is not None else "—"


def _display_width(text: str) -> int:
    """Return how many terminal columns ``text`` occupies.

    A CJK character takes two columns, so ``len()`` under-measures every Chinese
    label and the ``--lang zh`` / ``--lang both`` tables come out ragged.
    Ambiguous-width characters (the em dash used for an empty cell) are counted
    as one column, which is what a non-CJK-locale terminal renders.
    """
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    """Left-justify ``text`` to ``width`` display columns (CJK-aware ``ljust``)."""
    return text + " " * max(0, width - _display_width(text))


def _ascii_table(headers: List[str], rows: List[List[str]]) -> str:
    """Render a simple ASCII table (no external deps)."""
    widths = [_display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], _display_width(cell))

    def sep() -> str:
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def line(cells: List[str]) -> str:
        return (
            "| "
            + " | ".join(_pad(cell, widths[i]) for i, cell in enumerate(cells))
            + " |"
        )

    out = [sep(), line(headers), sep()]
    out.extend(line(row) for row in rows)
    out.append(sep())
    return "\n".join(out)


def render_human(
    result: ScoreResult, lang: str = "en", version: Optional[str] = None
) -> str:
    """Render the human-readable report (ASCII table + summary).

    :param lang: ``'en'`` (default), ``'zh'``, or ``'both'`` for bilingual
        headers, dimension names, and maturity level labels.
    :param version: questionnaire version to stamp on the report. Results are
        only comparable within one version, so a report that will be pasted
        into a deck or archived should always carry it. ``None`` omits the line.
    """
    headers = [
        ui(lang, "h_dimension"),
        ui(lang, "h_score"),
        ui(lang, "h_answered"),
        ui(lang, "h_get_rate"),
        ui(lang, "h_level"),
        ui(lang, "h_d_ratio"),
    ]
    rows: List[List[str]] = []
    for res in result.dimensions:
        dim_cell = f"{res.dimension} {dimension_name(res.dimension, lang)}"
        if not res.applicable:
            rows.append(
                [dim_cell, "—", "0", not_applicable_label(lang), "—", "—"]
            )
            continue
        level = f"{res.level_code} {level_label(res.level_code, lang)}"
        rows.append(
            [
                dim_cell,
                str(res.score),
                str(res.n_answered),
                _fmt_pct(res.get_rate),
                level,
                _fmt_ratio(res.d_ratio),
            ]
        )

    lines: List[str] = [ui(lang, "title")]
    if version:
        lines.append(f"{ui(lang, 'questionnaire')}: v{version}")
    lines.append("")
    lines.append(_ascii_table(headers, rows))
    lines.append("")

    o = result.overall
    if o.n_answered > 0:
        lines.append(
            f"{ui(lang, 'overall')}: "
            f"{ui(lang, 'total_score')}={o.total_score}  "
            f"{ui(lang, 'answered')}={o.n_answered}  "
            f"{ui(lang, 'get_rate')}={_fmt_pct(o.get_rate)}  "
            f"{ui(lang, 'level')}={o.level_code} "
            f"{level_label(o.level_code, lang)}  "
            f"{ui(lang, 'd_ratio')}={_fmt_ratio(o.d_ratio)}"
        )
    else:
        lines.append(ui(lang, "no_answers"))

    if o.weighted_get_rate is not None:
        lines.append(
            f"{ui(lang, 'weighted')}: "
            f"{ui(lang, 'get_rate')}={_fmt_pct(o.weighted_get_rate)}  "
            f"{ui(lang, 'level')}={o.weighted_level_code} "
            f"{level_label(o.weighted_level_code, lang)}"
        )

    if result.warnings:
        lines.append("")
        lines.append(ui(lang, "warnings"))
        lines.extend(f"  - {w}" for w in result.warnings)

    return "\n".join(lines)


def result_to_dict(
    result: ScoreResult, version: Optional[str] = None
) -> Dict[str, object]:
    """Convert a ScoreResult into a JSON-serializable dict.

    Labels are emitted for BOTH locales (``*_zh`` / ``*_en``) so a downstream
    report generator can render either language without re-scoring.

    ``questionnaire_version`` is included so an archived result stays
    interpretable: scores are only comparable within one version of the
    question bank.
    """
    dims: List[Dict[str, object]] = []
    for res in result.dimensions:
        code = res.level_code
        dims.append(
            {
                "dimension": res.dimension,
                "dimension_name_zh": DIMENSION_NAMES.get(res.dimension, {}).get("zh"),
                "dimension_name_en": DIMENSION_NAMES.get(res.dimension, {}).get("en"),
                "score": res.score,
                "n_answered": res.n_answered,
                "n_na": res.n_na,
                "applicable": res.applicable,
                "get_rate": res.get_rate,
                "level_code": code,
                "level_label": res.level_label,
                "level_label_zh": level_label(code, "zh"),
                "level_label_en": level_label(code, "en"),
                "not_applicable_label": None if res.applicable else NOT_APPLICABLE_LABEL,
                "not_applicable_label_zh": (
                    None if res.applicable else NOT_APPLICABLE_LABELS["zh"]
                ),
                "not_applicable_label_en": (
                    None if res.applicable else NOT_APPLICABLE_LABELS["en"]
                ),
                "d_count": res.d_count,
                "d_ratio": res.d_ratio,
            }
        )
    o = result.overall
    overall: Dict[str, object] = {
        "total_score": o.total_score,
        "n_answered": o.n_answered,
        "get_rate": o.get_rate,
        "level_code": o.level_code,
        "level_label": o.level_label,
        "level_label_zh": level_label(o.level_code, "zh"),
        "level_label_en": level_label(o.level_code, "en"),
        "d_count": o.d_count,
        "d_ratio": o.d_ratio,
    }
    if o.weighted_get_rate is not None:
        overall["weighted_get_rate"] = o.weighted_get_rate
        overall["weighted_level_code"] = o.weighted_level_code
        overall["weighted_level_label"] = o.weighted_level_label
        overall["weighted_level_label_zh"] = level_label(o.weighted_level_code, "zh")
        overall["weighted_level_label_en"] = level_label(o.weighted_level_code, "en")
    return {
        "questionnaire_version": version,
        "dimensions": dims,
        "overall": overall,
        "warnings": result.warnings,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_weights(raw: Optional[str]) -> Optional[List[float]]:
    """Parse the --weights argument into a list of 6 floats, or None."""
    if raw is None:
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip() != ""]
    try:
        weights = [float(p) for p in parts]
    except ValueError as exc:
        raise ValidationError(f"--weights must be comma-separated floats: {exc}") from exc
    if len(weights) != len(DIMENSION_ORDER):
        raise ValidationError(
            f"--weights needs {len(DIMENSION_ORDER)} values, got {len(weights)}"
        )
    negative = [w for w in weights if w < 0]
    if negative:
        raise ValidationError(
            f"--weights must all be non-negative, got {negative} -- a negative "
            "weight would subtract a dimension's get-rate from the overall"
        )
    if sum(weights) <= 0:
        raise ValidationError(
            "--weights must not be all zero -- there would be nothing to weight by"
        )
    return weights


def build_parser() -> argparse.ArgumentParser:
    version = read_questionnaire_version()
    parser = argparse.ArgumentParser(
        description="Score an AI-Ready Data self-assessment (CSV or JSON answers)."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"AI-Ready Data questionnaire v{version or 'unknown'}",
        help="Show the questionnaire version this checkout scores against.",
    )
    parser.add_argument("answers", help="Path to answers file (.csv or .json)")
    parser.add_argument(
        "--weights",
        help="Comma-separated 6 floats w1..w6; enables the weighted overall.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit a machine-readable JSON result instead of the human table.",
    )
    parser.add_argument(
        "--lang",
        choices=LANG_CHOICES,
        default="en",
        help=(
            "Output language for the human-readable report: "
            "'en' (default), 'zh', or 'both' (bilingual English / 中文). "
            "JSON output always carries both locales."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Error (exit 2) on unknown/missing questions rather than warn.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns an exit code (0 ok, 2 validation error)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        weights = parse_weights(args.weights)
        raw_rows = load_answers(args.answers)
        result = score_answers(raw_rows, weights=weights, strict=args.strict)
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    version = read_questionnaire_version()
    if args.as_json:
        print(
            json.dumps(
                result_to_dict(result, version=version), ensure_ascii=False, indent=2
            )
        )
    else:
        print(render_human(result, lang=args.lang, version=version))

    return 0


if __name__ == "__main__":
    sys.exit(main())
