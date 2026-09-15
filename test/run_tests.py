#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Run the full test suite and write the results into ``test/results/``.

Produces three artifacts, so the run is inspectable without re-running it:

  test/results/latest.txt   verbatim unittest output (verbose)
  test/results/latest.json  machine-readable summary (counts, per-test status)
  test/results/summary.md   short bilingual (中文 / English) markdown summary

Usage (from anywhere):

    python3 test/run_tests.py            # run everything, write artifacts
    python3 test/run_tests.py --quiet    # write artifacts, minimal stdout

Exit code is 0 when every test passes, 1 otherwise -- so CI can gate on it.
Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import platform
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = REPO_ROOT / "test"
RESULTS_DIR = TEST_DIR / "results"

for _sub in ("scoring", "scripts"):
    _p = str(REPO_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _read_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def _outcome_rows(result: unittest.TestResult) -> List[Dict[str, str]]:
    """Flatten a TestResult into per-test status rows."""
    rows: List[Dict[str, str]] = []
    for test, trace in result.failures:
        rows.append({"test": str(test), "status": "FAIL", "detail": trace.strip()})
    for test, trace in result.errors:
        rows.append({"test": str(test), "status": "ERROR", "detail": trace.strip()})
    for test, reason in result.skipped:
        rows.append({"test": str(test), "status": "SKIP", "detail": reason})
    for test in getattr(result, "unexpectedSuccesses", []):
        rows.append({"test": str(test), "status": "UNEXPECTED_PASS", "detail": ""})
    return rows


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the test suite and write results into test/results/."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not echo the full unittest output to stdout.",
    )
    args = parser.parse_args(argv)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(TEST_DIR), top_level_dir=str(REPO_ROOT))

    buffer = io.StringIO()
    runner = unittest.TextTestRunner(stream=buffer, verbosity=2)
    started_at = _dt.datetime.now().astimezone()
    t0 = time.perf_counter()
    result = runner.run(suite)
    duration = time.perf_counter() - t0

    output = buffer.getvalue()
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(
        result.skipped
    )
    ok = result.wasSuccessful()

    header = (
        f"AI-Ready Data — test run / 测试运行\n"
        f"timestamp    : {started_at.isoformat()}\n"
        f"questionnaire: v{_read_version()}\n"
        f"python       : {platform.python_version()} ({platform.system()} "
        f"{platform.machine()})\n"
        f"duration     : {duration:.3f}s\n"
        f"result       : {'PASS' if ok else 'FAIL'}  "
        f"(run={result.testsRun} passed={passed} "
        f"failed={len(result.failures)} errors={len(result.errors)} "
        f"skipped={len(result.skipped)})\n"
        + "=" * 72
        + "\n\n"
    )

    # 1. verbatim output
    (RESULTS_DIR / "latest.txt").write_text(header + output, encoding="utf-8")

    # 2. machine-readable summary
    payload: Dict[str, Any] = {
        "timestamp": started_at.isoformat(),
        "questionnaire_version": _read_version(),
        "python_version": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "duration_seconds": round(duration, 3),
        "success": ok,
        "counts": {
            "run": result.testsRun,
            "passed": passed,
            "failed": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
        },
        "non_passing": _outcome_rows(result),
    }
    (RESULTS_DIR / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 3. bilingual markdown summary
    status_zh = "通过" if ok else "失败"
    status_en = "PASS" if ok else "FAIL"
    md = [
        "# Test Results / 测试结果",
        "",
        f"- Status / 状态: **{status_en} / {status_zh}**",
        f"- Timestamp / 运行时间: `{started_at.isoformat()}`",
        f"- Questionnaire version / 问卷版本: `v{_read_version()}`",
        f"- Python: `{platform.python_version()}` "
        f"({platform.system()} {platform.machine()})",
        f"- Duration / 耗时: `{duration:.3f}s`",
        "",
        "| Metric / 指标 | Count / 数量 |",
        "|---|---|",
        f"| Run / 总计 | {result.testsRun} |",
        f"| Passed / 通过 | {passed} |",
        f"| Failed / 失败 | {len(result.failures)} |",
        f"| Errors / 错误 | {len(result.errors)} |",
        f"| Skipped / 跳过 | {len(result.skipped)} |",
        "",
    ]
    non_passing = _outcome_rows(result)
    if non_passing:
        md += ["## Non-passing tests / 未通过的测试", ""]
        for row in non_passing:
            md.append(f"- `{row['test']}` — **{row['status']}**")
        md.append("")
    else:
        md += ["All tests passed. / 所有测试通过。", ""]
    md += [
        "## Reproduce / 复现",
        "",
        "```bash",
        "python3 test/run_tests.py",
        "```",
        "",
        "Full output / 详细输出见: `latest.txt` · `latest.json`",
        "",
    ]
    (RESULTS_DIR / "summary.md").write_text("\n".join(md), encoding="utf-8")

    if not args.quiet:
        print(header + output, end="")
    print(
        f"[run_tests] {'PASS' if ok else 'FAIL'} — "
        f"{passed}/{result.testsRun} passed. "
        f"Artifacts written to {RESULTS_DIR.relative_to(REPO_ROOT)}/ "
        f"(latest.txt, latest.json, summary.md)"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
