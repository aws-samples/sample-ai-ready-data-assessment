<!--
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

## What changed and why / 改动内容与原因

<!-- One or two paragraphs. Link the Issue if this is a question change:
     a question proposal must be discussed and finalised in an Issue first.
     题目类改动必须先在 Issue 里讨论定稿，请在此关联 Issue。 -->

Closes #

## Type / 类型

- [ ] Question content / 题库内容 — **affects the questionnaire version**
- [ ] Scoring logic / 打分逻辑
- [ ] Bug fix / 缺陷修复
- [ ] Translation, i18n / 翻译
- [ ] Visualization, reporting / 可视化与报告
- [ ] Documentation / 文档

## Local validation / 本地验证

Paste the output. All of these must pass before review / 全部通过后再提交评审：

```bash
python3 scripts/check_modules.py          # questionnaire integrity + cross-locale parity
python3 test/run_tests.py                 # full unit test suite
python3 scripts/check_release_ready.py    # publication gate
python3 scoring/score.py scoring/answers.example.csv --strict
```

<details>
<summary>Output / 输出</summary>

```
(paste here)
```

</details>

## Questionnaire version / 问卷版本

- [ ] This PR does **not** affect the questionnaire version / 不影响问卷版本

If it does, confirm each item / 若影响，请逐项确认（见 `CONTRIBUTING.md`）:

- [ ] `VERSION` updated (MAJOR / MINOR / PATCH per the rules)
- [ ] `questionnaire-v…` badge updated in **both** `README.md` and `README.zh.md`
- [ ] `version:` updated in `CITATION.cff` — all four agree with `VERSION`
- [ ] Sample report blocks in both READMEs regenerated (`test_docs_consistency.py` fails until they match)
- [ ] `CHANGELOG.md` entry added, stating whether it touches the **questionnaire** or only the **tooling**
- [ ] For a MAJOR change: explained why old results are no longer comparable, with migration guidance

## Both locales / 双语

- [ ] `modules/` and `zh/modules/` stay in parity (same filenames, dimension ids, question counts)
- [ ] Documentation changes applied to both `*.md` and `*.zh.md`

## Licensing / 许可

- [ ] I confirm my contribution is released under [Apache-2.0](../blob/main/LICENSE) for code and [CC BY 4.0](../blob/main/LICENSE-CONTENT) for content, and that I have not committed a real answers file.
