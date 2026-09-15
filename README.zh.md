# AI-Ready Data · 企业自检工具 (Enterprise Self-Assessment Toolkit)

**🌐 Language / 语言:** [English](./README.md) · **简体中文**

[![CI](https://github.com/aws-samples/sample-ai-ready-data-assessment/actions/workflows/ci.yml/badge.svg)](https://github.com/aws-samples/sample-ai-ready-data-assessment/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Content: CC BY 4.0](https://img.shields.io/badge/Content-CC_BY_4.0-lightgrey.svg)](./LICENSE-CONTENT)
[![Questionnaire](https://img.shields.io/badge/questionnaire-v1.0.0-green.svg)](./VERSION)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

一个开源的 **“AI-Ready Data” 企业数据能力成熟度自检工具**。它帮助企业判断：为 AI 场景建设和运营的数据能力，在**成本与价值、数据质量、平台运维、组织人才、治理信任、安全合规**六个维度上，是否已经达到 “AI-Ready” 的水平。

- **45 道题**，分布在 6 个维度，每题从 A/B/C/D/N-A 五个选项中单选。
- 题库以 **Markdown** 呈现（人类可读 + 机器可解析），与打分逻辑解耦。
- **打分与成熟度分级由脚本自动计算** —— 支持 N/A 豁免、维度得分率、L1–L4 成熟度分级、D 档占比。

> 设计参考了公开的开源成熟度评估项目的通行做法（如 OWASP SAMM / DSOMM：把**模型内容**与**打分工具**分开维护、对问卷做**版本化**以保证跨版本可比、内容与代码采用**不同许可证**）。

---

## 目录结构

```
sample-ai-ready-data-assessment/
├── modules/                         # 题库：**英文**（默认内容源），每个维度一个 Markdown 文件
│   ├── 01-cost-and-business-value.md        (维度1 成本与业务价值 · 6题)
│   ├── 02-data-foundation-and-quality.md    (维度2 数据基础与质量 · 12题)
│   ├── 03-platform-architecture-and-ops.md  (维度3 平台架构与运维 · 12题)
│   ├── 04-organization-and-talent.md        (维度4 组织与人才 · 5题)
│   ├── 05-governance-and-trust.md           (维度5 治理与信任 · 5题)
│   └── 06-security-and-compliance.md        (维度6 安全与合规 · 5题)
├── zh/                              # 中文 locale
│   └── modules/                     #   中文题库（与 modules/ 一一对应）
├── scoring/                         # 打分工具（无第三方依赖）
│   ├── score.py                     #   打分 / 分级脚本
│   ├── answers.example.csv          #   作答样例 (CSV)
│   └── answers.example.json         #   作答样例 (JSON)
├── scripts/                         # 维护脚本
│   ├── check_modules.py             #   题库完整性校验（中英双 locale）
│   └── check_release_ready.py       #   发布前检查（打 tag 之前运行）
├── test/                            # 单元测试
│   ├── test_score.py                #   打分逻辑测试
│   ├── test_check_modules.py        #   题库完整性校验测试
│   ├── test_docs_consistency.py     #   文档与实际产物一致性守卫测试
│   ├── run_tests.py                 #   测试运行器（结果写入 results/）
│   └── results/                     #   运行器生成（已 git-ignore）
├── .github/                         # Issue / PR 模板、CI 配置、Dependabot
├── SCORING.md                       # 打分与分级机制的完整说明（英文权威版）
├── CONTRIBUTING.md                  # 贡献指南 + 提交 PR 的路径
├── CODE_OF_CONDUCT.md               # 行为准则
├── SECURITY.md                      # 安全漏洞上报方式
├── CHANGELOG.md                     # 问卷与工具的变更历史
├── LICENSE                          # 代码许可证 (Apache-2.0)
├── LICENSE-CONTENT                  # 题库/文档内容许可证 (CC BY 4.0)
├── NOTICE                           # 仓库各部分分别适用哪个许可证
├── CITATION.cff                     # 引用本工具的方式
├── *.zh.md                          # 上述每份文档的中文镜像
└── VERSION                          # 问卷版本号
```

## 六个维度

| 维度 | 名称 | 题数 | 理论满分 |
|---|---|---|---|
| 1 | 成本与业务价值 | 6 | 24 |
| 2 | 数据基础与质量 | 12 | 48 |
| 3 | 平台架构与运维 | 12 | 48 |
| 4 | 组织与人才 | 5 | 20 |
| 5 | 治理与信任 | 5 | 20 |
| 6 | 安全与合规 | 5 | 20 |
| **合计** | | **45** | **180** |

---

## 快速开始

### 1. 作答

打开 `modules/` 下的每个维度文件，对每道题选出最贴近你企业现状的一项（A / B / C / D，或 `N/A` 表示该能力/场景当前不存在）。

把答案填进一个作答文件，两种格式任选其一。最快的起步方式是复制一份样例再改答案 —— 它已包含全部 45 行和正确的题号：

```bash
cp scoring/answers.example.csv my-answers.csv     # 然后只改 answer 列
```

**CSV**（`dimension,question,answer` 三列，见 `scoring/answers.example.csv`）：

```csv
dimension,question,answer
dim1,Q1,C
dim1,Q2,B
...
dim5,Q3,N/A
```

**JSON**（维度 → 题号 → 答案 的嵌套对象，见 `scoring/answers.example.json`）：

```json
{
  "dim1": { "Q1": "C", "Q2": "B", "...": "..." },
  "dim5": { "Q3": "N/A" }
}
```

### 2. 打分

脚本仅依赖 Python 3 标准库，无需安装任何东西：

```bash
cd scoring
python3 score.py answers.example.csv                # 默认输出英文
python3 score.py answers.example.csv --lang zh      # 中文报告
```

中文输出示例（`--lang zh`）：

```
AI-Ready Data — 自检结果
问卷版本: v1.0.0

+---------------------+------+--------+----------+-------------+---------+
| 维度                | 得分 | 作答数 | 得分率   | 成熟度层级  | D档占比 |
+---------------------+------+--------+----------+-------------+---------+
| dim1 成本与业务价值 | 10   | 6      | 41.7%    | L2 初步实践 | 16.7%   |
| dim2 数据基础与质量 | 22   | 12     | 45.8%    | L2 初步实践 | 16.7%   |
| dim3 平台架构与运维 | 21   | 11     | 47.7%    | L2 初步实践 | 18.2%   |
| dim4 组织与人才     | 11   | 5      | 55.0%    | L3 基本达标 | 20.0%   |
| dim5 治理与信任     | —    | 0      | 暂不适用 | —           | —       |
| dim6 安全与合规     | 9    | 5      | 45.0%    | L2 初步实践 | 20.0%   |
+---------------------+------+--------+----------+-------------+---------+

总体: 总分=73  作答数=39  得分率=46.8%  层级=L2 初步实践  D档占比=17.9%
```

> 报告**默认输出英文**。用 `--lang zh` 切换为中文，或 `--lang both` 输出中英双语（English / 中文）表格；`--json` 的结果始终同时携带中英标签，便于下游生成任一语言的报告。

常用参数：

```bash
python3 score.py answers.csv                           # 英文报告（默认）
python3 score.py answers.csv --lang zh                 # 仅中文报告
python3 score.py answers.csv --lang both               # 中英双语报告
python3 score.py answers.csv --json                    # 输出机器可读的 JSON 结果（同时含中英标签）
python3 score.py answers.csv --weights 1,1,1,1,2,2      # 行业/阶段加权（例如金融加重治理与安全）
python3 score.py answers.csv --strict                  # 遇到未知/缺失题目时报错而非告警
python3 score.py --version                             # 打印问卷版本号后退出
```

> **每份报告都会带上问卷版本号**（上面的 `问卷版本: v1.0.0`；`--json` 输出中对应
> `questionnaire_version` 字段）。请把它和结果一起保留：得分只在同一个问卷版本内可比，
> 详见 [`SCORING.zh.md`](./SCORING.zh.md)。版本号读取自 [`VERSION`](./VERSION)。
>
> `--strict` 会把所有告警升级为错误，覆盖：未知维度、题数与维度不符、同一题重复作答、
> 以及题号在该维度中不存在（例如 `dim1,Q77,C` —— `dim1` 只有 `Q1`–`Q6`）。流水线里建议
> 加上它；不加时这些问题只作为告警提示，打分照常继续。

---

## 打分机制（摘要）

完整说明见 [`SCORING.zh.md`](./SCORING.zh.md)。

**单题分值**：`A=0`（未起步）、`B=1`（初步实践）、`C=2`（基本达标）、`D=4`（成熟领先）、`N/A` 不计分且不计入分母。

> C→D 之所以是 **2 分**（而非等距的 1 分）：A→B→C 是“从无到有点意识到基本成体系”的量变，C→D 是“体系真正跑通、自动化、可持续验证”的质变，门槛更陡。放大这一档差距，能避免“少数题冲到 D 就拉高整体印象分”。

**得分率**（动态分母，处理 N/A 豁免）：

```
维度得分率 = 维度得分 / (该维度实际作答题数 × 4) × 100%
```

**成熟度分级**（对总体与每个维度分别套用同一套区间）：

| 层级 | 得分率区间 | 含义 |
|---|---|---|
| L1 未起步 | `[0%, 25%)` | 能力基本空白 |
| L2 初步实践 | `[25%, 50%)` | 有零散实践，未成体系 |
| L3 基本达标 | `[50%, 75%)` | 核心机制建立，但自动化/验证/闭环有缺口 |
| L4 成熟领先 | `[75%, 100%]` | 体系化、自动化、可追溯、有持续改进闭环 |

**特殊情形**：若某维度全部作答为 N/A，该维度**不计得分率、不参与雷达图对比**，报告标注“暂不适用”，而非显示 0%（显示 0% 会被误读为“做得很差”）。

---

## 如何解读结果

- 先看**总体层级**定位整体水位，再看**各维度独立层级**找短板 —— 总分会掩盖结构性失衡（比如平台很强但治理空白）。
- 关注 **D 档占比**：它比得分率更能说明“有多少能力真正达到了体系化 + 自动化 + 可验证闭环”，而不是被大量 C 档“平均”出一个看起来还行的分数。
- 建议用**雷达图**（六个轴为六个维度的得分率 0–100%）呈现，跨维度可比。

---

## 参与贡献

题库、打分逻辑、翻译、可视化都欢迎贡献。**提交 PR 的完整路径见 [`CONTRIBUTING.zh.md`](./CONTRIBUTING.zh.md)**（含新增/修改题目的提案流程与问卷版本化规则）。

参与本项目需遵守[行为准则](./CODE_OF_CONDUCT.zh.md)。安全问题请按 [`SECURITY.zh.md`](./SECURITY.zh.md) 的方式上报，**不要**提交公开 issue。重要变更记录在 [`CHANGELOG.md`](./CHANGELOG.md)。

## 许可证

- **代码**（`scoring/` 等）：[Apache License 2.0](./LICENSE)
- **题库与文档内容**（`modules/`、`*.md`）：[CC BY 4.0](./LICENSE-CONTENT)

分开授权是这类评估工具的通行做法：代码可自由集成，内容在署名前提下可自由传播与改编。

## 引用

如在报告或研究中使用本工具，见 [`CITATION.cff`](./CITATION.cff)。
