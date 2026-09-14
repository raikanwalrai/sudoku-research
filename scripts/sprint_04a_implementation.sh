#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${PYTHON_BIN:-}" ]]; then
    if [[ -x "$ROOT/.venv/bin/python" ]]; then
        PYTHON_BIN="$ROOT/.venv/bin/python"
    else
        PYTHON_BIN="python3"
    fi
fi

echo "===== SPRINT 04A: CANONICAL IDENTITY IMPLEMENTATION ====="

echo
echo "===== PYTHON COMPILE CHECK ====="
"$PYTHON_BIN" -m compileall -q src
echo "[PASS] Python compilation"

echo
echo "===== IDENTITY TESTS ====="
"$PYTHON_BIN" -m pytest -q tests/test_dataset.py
echo "[PASS] Sprint 04A dataset identity tests"

echo
echo "===== FULL TEST SUITE ====="
"$PYTHON_BIN" -m pytest -q
echo "[PASS] Full test suite"

echo
echo "===== DIFF CHECK ====="
git diff --check
echo "[PASS] Git diff check"

echo
echo "===== SPRINT 04A VALIDATION COMPLETE ====="
