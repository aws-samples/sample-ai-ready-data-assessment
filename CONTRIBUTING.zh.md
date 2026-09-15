# 贡献指南 (Contributing)

**🌐 Language / 语言:** [English](./CONTRIBUTING.md) · **简体中文**

感谢你愿意让 **AI-Ready Data 企业自检工具** 变得更好！本文件说明**如何提交贡献**，以及针对“评估问卷”这类项目特有的规则（尤其是**新增/修改题目**和**问卷版本化**）。

---

## 可以贡献什么

| 类型 | 说明 | 影响问卷版本？ |
|---|---|---|
| 📝 **题目内容** | 新增题目、修改选项措辞、调整维度归属 | **是**（见下方版本化规则） |
| 🔢 **打分逻辑** | `scoring/score.py` 的功能、参数、输出 | 否（除非改变计分口径） |
| 🐛 **Bug 修复** | 脚本报错、解析错误、边界情况 | 否 |
| 🌐 **翻译 / i18n** | 英文或其他语言版本的题库 | 否 |
| 📊 **可视化 / 报告** | 雷达图、HTML 报告生成器等 | 否 |
| 📚 **文档** | README / SCORING 的澄清与补充 | 否 |

---

## 提交 PR 的路径（Pull Request Workflow）

> 默认分支：`main`。请**不要**直接向 `main` 推送，一律通过 PR。

1. **Fork** 本仓库到你自己的账号。
2. **Clone** 你的 fork 并创建特性分支：
   ```bash
   git clone git@github.com:<your-username>/sample-ai-ready-data-assessment.git
   cd sample-ai-ready-data-assessment
   git checkout -b feat/<简短描述>          # 例如 feat/add-dim2-lineage-question
   ```
3. **改动**。若涉及题库，务必同步更新对应的 `modules/*.md` 与（如需要）`scoring/` 里的样例。
4. **本地验证**（提交前必须通过）。需要 Python **3.9 及以上**，仅用标准库，无需安装任何依赖：
   ```bash
   python3 scripts/check_modules.py          # 题库完整性 + 跨 locale 一致性
   python3 test/run_tests.py                 # 全部单元测试，结果写入 test/results/
   python3 scripts/check_release_ready.py    # 发布前检查（见发布清单）
   cd scoring
   python3 score.py answers.example.csv       # 样例可正常打分
   python3 score.py answers.example.json      # JSON 路径也要正常
   python3 score.py answers.example.csv --strict   # 确认没有遗留告警
   ```
   如果你修改了题数，`test/test_score.py` 与 `test/test_check_modules.py` 中对应维度的期望题数也要更新。

   `test/test_docs_consistency.py` 会重新生成两份 README 中展示的示例报告并与真实输出逐字比对，因此**只要改动了报告格式或示例作答，README 里的示例输出块就必须同步重新生成**。测试失败信息会直接给出应该粘贴的内容。
5. **提交**（使用清晰的 commit 信息，推荐 [Conventional Commits](https://www.conventionalcommits.org/)）：
   ```bash
   git add -A
   git commit -m "feat(dim2): add question on feature-store freshness SLO"
   git push origin feat/<简短描述>
   ```
6. **发起 PR**，目标是本仓库的 `main` 分支。PR 描述请说明：
   - **改了什么、为什么**；
   - 是否**影响问卷版本**（若是，勾选下方版本化清单）；
   - 本地验证结果（贴出测试 / 打分输出）。
7. 通过 **CI**（测试 + 题数一致性校验）与至少一位维护者 **review** 后合并。

---

## 题库格式约定（务必遵守，否则脚本无法解析）

每个 `modules/NN-*.md` 文件必须满足：

- 文件顶部有 YAML front-matter：
  ```yaml
  ---
  id: dim2                 # dim1..dim6
  title: 数据基础与质量
  dimension_number: 2
  question_count: 12       # 必须与文件内 ### Q 数量一致
  ---
  ```
  英文源文件 `modules/` 的 front-matter 中 `title` 为英文（`title: Data Foundation & Quality`），
  其余字段（`id`、`dimension_number`、`question_count`）两个 locale 必须完全一致。
  `scripts/check_modules.py` 会强制校验这种一致性 —— 两个 locale 的文件名、维度 id、
  题数必须相同。
- 每道题以 `### Q<n>` 独占一行作为标题，题号在**该维度内**从 `Q1` 递增。维度内的分组标题使用 `## <n>.<m> 分组名`，使题目层级嵌套在其之下。
- 紧接一个**加粗**的题干行，然后是**恰好 5 个**选项，每个选项以字母开头：
  ```
  - A. ...
  - B. ...
  - C. ...
  - D. ...
  - N/A. ...
  ```
- 语义固定：**A=未起步，B=初步实践，C=基本达标，D=成熟领先，N/A=不适用**。新增题目的四个层级必须遵循这套语义梯度（量变 A→B→C，质变 C→D）。

---

## 新增 / 修改题目：提案流程

题目改动会影响所有使用者的评分口径，因此比普通代码改动更谨慎：

1. **先开 Issue 提案**（使用 *Question Proposal* 模板），说明：
   - 提议的题干、四个选项 + N/A 的措辞；
   - 归属维度与理由；
   - 它衡量的能力，为什么值得单独成题（避免与现有题重复）。
2. 维护者与社区在 Issue 中讨论、定稿措辞。
3. 定稿后再提 PR，PR 关联该 Issue。
4. **不要在一个 PR 里混入多个不相关的题目改动** —— 每个题目改动应可独立评审与回滚。

---

## 问卷版本化（保证跨版本可比）

评分结果只有在**同一问卷版本**下才可比较。因此：

- 版本号记录在根目录 [`VERSION`](./VERSION)，遵循语义化版本 `MAJOR.MINOR.PATCH`：
  - **MAJOR**：改变了计分口径、维度结构、或删改题目导致旧作答不可比（例如维度权重默认值变更、选项分值变更）。
  - **MINOR**：新增题目，或在**不改变既有题目分值**的前提下扩展（旧作答仍可解释，但满分变化）。
  - **PATCH**：措辞澄清、错别字、翻译、文档、脚本 bug 修复（不影响任何得分）。
- **任何影响版本的 PR 必须**：
  - [ ] 更新 `VERSION`；
  - [ ] 同步更新 `README.md` 与 `README.zh.md` **两份**文件中的 `questionnaire-v…` badge，以及 `CITATION.cff` 中的 `version:` —— 四处必须与 `VERSION` 一致；
  - [ ] 重新生成两份 README 中的示例报告块（其中带有版本号行，不同步 `test/test_docs_consistency.py` 会失败）；
  - [ ] 在 `CHANGELOG.md` 中新增条目，并说明本次改动涉及**问卷**还是仅涉及**工具**；
  - [ ] 在 PR 描述中总结改动（日期、改了什么、影响的维度/题号），以便写入 GitHub Release notes；
  - [ ] 若为 MAJOR，在 PR 描述中说明“为何旧结果不再可比”以及迁移建议。

### 发布清单（维护者）

打 tag 之前：

```bash
python3 scripts/check_modules.py
python3 test/run_tests.py
python3 scripts/check_release_ready.py    # 必须退出码为 0
```

`check_release_ready.py` 专门拦截“只在发布时才会暴露”的问题：未替换的仓库 owner
占位符、在私有工作副本里无害但公开后即成为泄漏的内网主机名或 URL、`.py` 文件缺少
`SPDX-License-Identifier` 头、`VERSION` / README badge / `CITATION.cff` 三处版本号
不一致、缺少任一 locale 的必需文档、以及误提交的本地产物（`.DS_Store`、生成的
`test/results/`、真实作答文件 —— 最后这一项记录的是某个组织的能力短板，绝不能公开）。
CI 在每次 push 时都会运行它以便及早发现，并在打 tag 时**强制**通过。

---

## 行为准则

本项目遵循 [Amazon 开源行为准则](./CODE_OF_CONDUCT.zh.md)。
请保持友善、就事论事。评估口径的分歧用数据和场景来讨论，而不是立场。

## 安全问题上报

安全问题请**不要**提交公开 GitHub issue，上报路径见 [`SECURITY.zh.md`](./SECURITY.zh.md)。

## 许可

- 提交到 `scoring/` 等**代码**的贡献，按 [Apache-2.0](./LICENSE) 授权。
- 提交到 `modules/` 及文档等**内容**的贡献，按 [CC BY 4.0](./LICENSE-CONTENT) 授权。

提交 PR 即表示你同意你的贡献在上述相应许可证下发布。
