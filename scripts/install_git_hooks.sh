#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.githooks"
HOOK="$HOOKS_DIR/pre-push"

if [ ! -x "$HOOK" ]; then
    echo "[FAIL] Expected executable pre-push hook was not found:"
    echo "       $HOOK"
    exit 1
fi

git config core.hooksPath .githooks

echo "[PASS] Git hooks path configured:"
git config --get core.hooksPath

echo "[PASS] Pre-push hook installed:"
echo "       $HOOK"
