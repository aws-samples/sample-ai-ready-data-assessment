# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Test package for the AI-Ready Data assessment toolkit.

Adds the repository's ``scoring/`` and ``scripts/`` directories to ``sys.path``
so test modules can ``import score`` / ``import check_modules`` directly,
regardless of the directory unittest is invoked from.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

for _sub in ("scoring", "scripts"):
    _path = str(REPO_ROOT / _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)
