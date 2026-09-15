# Security Policy

**🌐 Language / 语言:** **English** · [简体中文](./SECURITY.zh.md)

## Reporting a potential security issue

If you discover a potential security issue in this project, please notify AWS /
Amazon Security via the
[vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/),
or directly by email to aws-security@amazon.com.

**Please do not create a public GitHub issue** for a suspected vulnerability,
and please do not open a pull request that demonstrates it.

## Scope

This is worth stating plainly, because it sets expectations for what is worth
reporting.

The toolkit is a Markdown question bank plus a scoring script that uses **only
the Python standard library**. It has **no third-party runtime dependencies**, no
network calls, no authentication, no persistence, and no server component. It
reads a local answers file and prints a report.

The realistic attack surface is therefore limited to how `scoring/score.py`
handles an untrusted **answers file**. In scope:

- crashes, hangs, or unbounded resource use when parsing a malformed or hostile
  CSV / JSON answers file;
- anything that causes the script to read or write a path outside the file
  explicitly passed on the command line;
- a scoring result that can be silently manipulated into being wrong — for
  example an answer file that inflates a score while `--strict` still exits 0.

Out of scope:

- disagreement with the assessment model itself (question wording, an option's
  maturity level, the C→D point gap). Those are content questions — open a
  *Question Proposal* issue instead, see [`CONTRIBUTING.md`](./CONTRIBUTING.md);
- the contents of a report you generate. Your answers file describes your own
  organization; treat the answers and the resulting report as internal material
  and do not commit them. The `.gitignore` already excludes `*answers*.csv` and
  `*answers*.json` for this reason.

## Supported versions

Fixes land on `main` and are described in [`CHANGELOG.md`](./CHANGELOG.md).
There are no long-lived maintenance branches; please report against the current
`main`.
