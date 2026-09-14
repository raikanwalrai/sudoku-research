#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
fi

echo "============================================================"
echo " SPRINT 03 — IMPLEMENTATION VALIDATION"
echo "============================================================"

echo
echo "===== PYTHON ====="
"$PYTHON_BIN" --version

echo
echo "===== COMPILE ====="
"$PYTHON_BIN" -m compileall -q src tests

echo
echo "===== TEST SUITE ====="
"$PYTHON_BIN" -m pytest -q

echo
echo "===== DIFF CHECK ====="
git diff --check

echo
echo "============================================================"
echo " SPRINT 03 IMPLEMENTATION VALIDATION PASSED"
echo "============================================================"
