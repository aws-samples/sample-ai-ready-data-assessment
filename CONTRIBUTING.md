# Contributing

**🌐 Language / 语言:** **English** · [简体中文](./CONTRIBUTING.zh.md)

Thank you for wanting to make the **AI-Ready Data Enterprise Self-Assessment Toolkit** better! This document explains **how to contribute**, along with the rules specific to an "assessment questionnaire" project (especially **adding/modifying questions** and **questionnaire versioning**).

---

## What You Can Contribute

| Type | Description | Affects questionnaire version? |
|---|---|---|
| 📝 **Question content** | Add questions, revise option wording, adjust dimension assignment | **Yes** (see the versioning rules below) |
| 🔢 **Scoring logic** | Features, options, and output of `scoring/score.py` | No (unless it changes the scoring basis) |
| 🐛 **Bug fixes** | Script errors, parsing errors, edge cases | No |
| 🌐 **Translation / i18n** | English or other-language versions of the question bank | No |
| 📊 **Visualization / reporting** | Radar charts, HTML report generators, etc. | No |
| 📚 **Documentation** | Clarifications and additions to README / SCORING | No |

---

## Pull Request Workflow

> Default branch: `main`. Please do **not** push directly to `main` — always go through a PR.

1. **Fork** this repository to your own account.
2. **Clone** your fork and create a feature branch:
   ```bash
   git clone git@github.com:<your-username>/sample-ai-ready-data-assessment.git
   cd sample-ai-ready-data-assessment
   git checkout -b feat/<short-description>          # e.g. feat/add-dim2-lineage-question
   ```
3. **Make your changes.** If they touch the question bank, be sure to also update the corresponding `modules/*.md` and (if needed) the samples under `scoring/`.
4. **Validate locally** (must pass before submitting). Python **3.9 or newer**, standard library only — nothing to install:
   ```bash
   python3 scripts/check_modules.py          # questionnaire integrity + cross-locale parity
   python3 test/run_tests.py                 # full unit test suite -> test/results/
   python3 scripts/check_release_ready.py    # publication gate (see the release checklist)
   cd scoring
   python3 score.py answers.example.csv       # sample scores correctly
   python3 score.py answers.example.json      # the JSON path works too
   python3 score.py answers.example.csv --strict   # no warnings left behind
   ```
   If you change the number of questions, update the expected question count in `test/test_score.py` and `test/test_check_modules.py` as well.

   `test/test_docs_consistency.py` regenerates the sample reports shown in both READMEs and diffs them against real output, so **any change to the report format or to the example answers means the README sample blocks must be regenerated**. The failure message tells you exactly what to paste.
5. **Commit** (use a clear commit message; [Conventional Commits](https://www.conventionalcommits.org/) recommended):
   ```bash
   git add -A
   git commit -m "feat(dim2): add question on feature-store freshness SLO"
   git push origin feat/<short-description>
   ```
6. **Open a PR** targeting this repository's `main` branch. In the PR description, please state:
   - **what changed and why**;
   - whether it **affects the questionnaire version** (if so, check the versioning checklist below);
   - your local validation results (paste the test / scoring output).
7. Merged after passing **CI** (tests + question-count consistency checks) and **review** by at least one maintainer.

---

## Question-Bank Format Conventions (must be followed, or the script cannot parse the file)

Every `modules/NN-*.md` file must satisfy:

- YAML front-matter at the top of the file:
  ```yaml
  ---
  id: dim2                 # dim1..dim6
  title: Data Foundation & Quality
  dimension_number: 2
  question_count: 12       # must match the number of ### Q entries in the file
  ---
  ```
  The `zh/modules/` counterpart carries the same `id`, `dimension_number`, and
  `question_count`, with `title` translated (`title: 数据基础与质量`).
  `scripts/check_modules.py` enforces this parity — the two locales must have
  the same filenames, the same dimension ids, and the same question counts.
- Each question uses `### Q<n>` on its own line as the heading, with the number incrementing from `Q1` **within that dimension**. Group headers within a dimension use `## <n>.<m> <name>` so that questions nest beneath them.
- Immediately followed by a **bold** stem line, then **exactly 5** options, each beginning with a letter:
  ```
  - A. ...
  - B. ...
  - C. ...
  - D. ...
  - N/A. ...
  ```
- The semantics are fixed: **A = not started, B = initial practice, C = basically compliant, D = mature and leading, N/A = not applicable**. A new question's four levels must follow this semantic gradient (quantitative change A→B→C, qualitative leap C→D).

---

## Adding / Modifying Questions: Proposal Process

Question changes affect the scoring basis for all users, so they are handled more cautiously than ordinary code changes:

1. **Open an Issue proposal first** (use the *Question Proposal* template), stating:
   - the proposed stem, the four options + N/A wording;
   - the assigned dimension and the reason;
   - the capability it measures and why it deserves to be its own question (to avoid duplicating an existing one).
2. Maintainers and the community discuss and finalize the wording in the Issue.
3. Only after the wording is finalized, submit a PR that links to the Issue.
4. **Do not mix multiple unrelated question changes into one PR** — each question change should be independently reviewable and revertible.

---

## Questionnaire Versioning (ensuring cross-version comparability)

Scoring results are only comparable under the **same questionnaire version**. Therefore:

- The version number is recorded in [`VERSION`](./VERSION) at the repository root, following semantic versioning `MAJOR.MINOR.PATCH`:
  - **MAJOR**: changes the scoring basis, the dimension structure, or deletes/modifies questions such that old answers are no longer comparable (e.g. a change to the default dimension weights, or a change to option values).
  - **MINOR**: adds questions, or extends without **changing the values of existing questions** (old answers are still interpretable, but the maximum score changes).
  - **PATCH**: wording clarifications, typos, translations, documentation, script bug fixes (does not affect any score).
- **Any version-affecting PR must**:
  - [ ] update `VERSION`;
  - [ ] update the `questionnaire-v…` badge in **both** `README.md` and `README.zh.md`, and `version:` in `CITATION.cff` — all four must agree with `VERSION`;
  - [ ] regenerate the sample report blocks in both READMEs (they carry the version line, and `test/test_docs_consistency.py` will fail until they match real output);
  - [ ] add a `CHANGELOG.md` entry stating whether it touches the **questionnaire** or only the **tooling**;
  - [ ] summarise the change in the PR description (the date, what changed, and the affected dimensions/question numbers) so it can be carried into the GitHub Release notes;
  - [ ] for a MAJOR change, explain in the PR description "why old results are no longer comparable" and provide migration guidance.

### Release checklist (maintainers)

Before tagging:

```bash
python3 scripts/check_modules.py
python3 test/run_tests.py
python3 scripts/check_release_ready.py    # must exit 0
```

`check_release_ready.py` is the gate that catches release-only mistakes: an
unreplaced repository-owner placeholder, an internal-only host name or URL that
was harmless in a private working copy, a missing `SPDX-License-Identifier`
header on a `.py` file, version drift between `VERSION`, the README badges and
`CITATION.cff`, a missing required document in either locale, and committed local
artifacts (a `.DS_Store`, generated `test/results/`, or a real answers file — the
last of these describes an organization's weak spots and must never be
published). CI runs it on every push for visibility and **enforces** it on tags.

---

## Code of Conduct

This project follows the [Amazon Open Source Code of Conduct](./CODE_OF_CONDUCT.md).
Please be kind and focus on the substance. Discuss disagreements about the scoring basis with data and scenarios, not positions.

## Reporting Security Issues

Please do **not** open a public GitHub issue for a security problem. See
[`SECURITY.md`](./SECURITY.md) for the reporting path.

## Licensing

- Contributions to **code** such as `scoring/` are licensed under [Apache-2.0](./LICENSE).
- Contributions to **content** such as `modules/` and the documentation are licensed under [CC BY 4.0](./LICENSE-CONTENT).

By submitting a PR, you agree that your contribution is released under the respective license above.
