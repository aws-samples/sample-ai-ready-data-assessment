# 安全策略

**🌐 Language / 语言:** [English](./SECURITY.md) · **简体中文**

## 如何上报潜在安全问题

如果你在本项目中发现潜在的安全问题，请通过
[AWS 漏洞上报页面](https://aws.amazon.com/security/vulnerability-reporting/)
通知 AWS / Amazon Security，或直接发送邮件至 aws-security@amazon.com。

**请不要为疑似漏洞创建公开的 GitHub Issue**，也请不要提交用于演示该漏洞的 Pull Request。

## 适用范围

这里把范围说清楚，是为了让“什么值得上报”有明确预期。

本工具由一套 Markdown 题库和一个**仅依赖 Python 标准库**的打分脚本组成，**没有任何第三方运行时依赖**，不发起网络请求，没有鉴权、没有持久化、没有服务端组件——它读取一个本地作答文件，然后打印一份报告。

因此真实的攻击面仅限于 `scoring/score.py` 如何处理**不可信的作答文件**。在范围内：

- 解析畸形或恶意构造的 CSV / JSON 作答文件时出现崩溃、挂起或资源无限增长；
- 任何导致脚本读写命令行显式传入之外路径的行为；
- 打分结果可被静默篡改为错误值——例如某个作答文件抬高了得分，而 `--strict` 仍然以 0 退出。

不在范围内：

- 对评估模型本身的分歧（题目措辞、某选项的档位归属、C→D 的分差）。这些属于内容问题，请改为提交 *Question Proposal* Issue，见 [`CONTRIBUTING.zh.md`](./CONTRIBUTING.zh.md)；
- 你自己生成的报告内容。作答文件描述的是你所在组织的现状，请把作答与报告视为内部材料，不要提交进仓库。`.gitignore` 已因此排除 `*answers*.csv` 与 `*answers*.json`。

## 版本支持

修复直接合入 `main`，并记录在 [`CHANGELOG.md`](./CHANGELOG.md) 中。本项目不维护长期支持分支，请基于当前 `main` 上报问题。
