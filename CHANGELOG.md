# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Two things are versioned in this repository and they are **not** the same:

- the **questionnaire**, whose version lives in [`VERSION`](./VERSION) and
  follows the rules in [`CONTRIBUTING.md`](./CONTRIBUTING.md#questionnaire-versioning-ensuring-cross-version-comparability).
  Scores are only comparable within one questionnaire version;
- the **tooling** (`scoring/`, `scripts/`, `test/`), which can change without
  affecting any score.

Each entry below states which of the two it touches.

## [Unreleased]

Questionnaire: **unchanged (1.0.0)** · Tooling only — no question wording,
option value, or band boundary changed, so every 1.0.0 score remains valid and
comparable.

### Fixed

- `score.py` no longer crashes with a traceback on a malformed answers file.
  Invalid JSON, a non-UTF-8 file, a directory, an unreadable path, and a
  pathologically nested JSON document (which exhausted the C stack via
  `RecursionError`) are now all reported as `validation error: ...` with exit
  code 2, which is what `SECURITY.md` documents as the contract.
- Chinese and bilingual report tables are no longer ragged. Column widths are
  measured in terminal columns via `unicodedata.east_asian_width` instead of
  in characters, so a CJK label counts as two columns. The `README.zh.md`
  sample block has been regenerated accordingly.
- A question id repeated within one dimension is now deduplicated — the last
  row wins, with a warning — instead of being scored twice and silently
  inflating that dimension.
- `read_questionnaire_version()` validates that `VERSION` looks like
  `MAJOR.MINOR.PATCH`. Copied out of the repository, `score.py` resolved its
  repo root to whatever directory sat above it and would stamp an unrelated
  `VERSION` file onto a report.
- `python3 test/test_score.py` ran only 32 of its 52 tests: an
  `if __name__ == "__main__"` block sat in the middle of the file, before five
  test classes were defined. Moved to the end. (`run_tests.py` was unaffected —
  it imports the module before collecting, so all tests always ran in CI.)

### Added

- `.github/` — CI workflow (unit tests, questionnaire integrity, and example
  scoring across Python 3.9–3.13; release gate advisory on pushes and enforced
  on tags), bilingual issue templates, PR template, and Dependabot for Actions.
- `.gitignore` — which `SECURITY.md` and both READMEs already described but the
  repository did not actually carry, so the documented protection for a real
  answers file was not in place.
- `check_release_ready.py` gained two checks: internal-only host names and URLs
  (the gate previously passed a checkout whose `CITATION.cff` still pointed at
  an internal git remote), and a required SPDX license header on every tracked
  `.py` file.
- `check_modules.py` now verifies that each question's bold stem number agrees
  with its `### Q<n>` heading, and that the stem exists at all.
- 16 more unit tests covering the fixes above (87 total).

### Changed

- Repository home is now
  <https://github.com/aws-samples/sample-ai-ready-data-assessment>; `CITATION.cff`
  and both `CONTRIBUTING` files referenced an internal host.
- Copyright and attribution are now Amazon.com, Inc. or its affiliates, with
  SPDX short-form headers (`SPDX-License-Identifier: Apache-2.0`) on all
  Python files, including `test/`, which previously carried none. Licensing is
  unchanged: Apache-2.0 for code, CC BY 4.0 for the question bank and docs.
- Maturity band tables in all four docs now use explicit interval notation
  (`[25%, 50%)`) rather than `25% – 50%`, which did not say which band owns a
  boundary value.

## [1.0.0] — 2026-08-30

Questionnaire: **1.0.0** (initial public release) · Tooling: initial public release

### Added

- 45-question assessment across six dimensions (6 / 12 / 12 / 5 / 5 / 5),
  authored in Markdown and decoupled from the scoring logic, in two locales:
  `modules/` (English, default content source) and `zh/modules/` (简体中文).
- `scoring/score.py` — N/A-aware scoring and L1–L4 maturity grading with
  per-dimension get-rates, D-tier ratio, optional `--weights`, CSV and JSON
  input, `--lang en|zh|both` reports, and `--json` machine-readable output
  carrying both locales.
- `scripts/check_modules.py` — questionnaire integrity gate: front-matter
  `question_count` agreement, clean `Q1..Qn` numbering, the exact five-option
  set per question, and **cross-locale parity** between `modules/` and
  `zh/modules/`.
- `test/` — 87 unit tests including docs-consistency guards that regenerate the
  README sample reports and diff them against real output, verify the maturity
  labels in all four docs match what the tool prints, and verify `VERSION`, the
  README badges, and `CITATION.cff` all agree.
- `scripts/check_release_ready.py` — release gate that fails on an unreplaced
  repository-owner placeholder, on version drift between `VERSION`, the README
  badges, and `CITATION.cff`, and on committed local artifacts such as a real
  answers file.
- Bilingual `README`, `SCORING`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, and
  `SECURITY` documents; bilingual issue and PR templates.
- Dual licensing: Apache-2.0 for code ([`LICENSE`](./LICENSE)), CC BY 4.0 for
  the question bank and documentation ([`LICENSE-CONTENT`](./LICENSE-CONTENT)),
  summarised in [`NOTICE`](./NOTICE).

### Notes for anyone comparing against a pre-release copy

These changed during release preparation and affect tooling behaviour, not any
question's score:

- reports now stamp the questionnaire version (`questionnaire: v1.0.0`), and
  `--json` output carries a `questionnaire_version` key;
- `--strict` now rejects a question id that does not exist in its dimension.
  Previously a typo such as `dim1,Q77,C` was scored silently;
- `--weights` now rejects negative values and an all-zero vector instead of
  accepting them and producing a meaningless or silently absent result;
- example answer files use uppercase question ids (`Q1`), matching the docs and
  the `### Q1` module headings;
- Python 3.9 is the supported floor (3.8 reached end-of-life in October 2024).
