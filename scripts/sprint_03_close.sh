#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
fi

echo "============================================================"
echo " SPRINT 03 — CLOSURE VALIDATION"
echo "============================================================"

echo
echo "===== REPOSITORY ====="
git rev-parse --show-toplevel
git branch --show-current
git status --short

echo
echo "===== PYTHON ====="
"$PYTHON_BIN" --version

echo
echo "===== IMPLEMENTATION VALIDATION ====="
bash scripts/sprint_03_implementation.sh

echo
echo "===== SECURITY SELF-TEST ====="
bash scripts/security_scan.sh --self-test

echo
echo "===== SECURITY WORKING TREE SCAN ====="
bash scripts/security_scan.sh --working-tree

echo
echo "===== SECURITY HEAD SCAN ====="
bash scripts/security_scan.sh --head

echo
echo "===== SECURITY HISTORY SCAN ====="
bash scripts/security_scan.sh --history

echo
echo "===== FINAL DIFF CHECK ====="
git diff --check

echo
echo "===== FINAL STATUS ====="
git status --short

echo
echo "============================================================"
echo " SPRINT 03 CLOSURE VALIDATION PASSED"
echo "============================================================"
