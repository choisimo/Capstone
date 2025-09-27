#!/usr/bin/env bash
# Pre-commit DocSync check
# Blocks commit if documentation sync validation fails.

set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

PYBIN="python3"
command -v python3 >/dev/null 2>&1 || PYBIN="python"

if [ -f "tools/doc_sync/cli.py" ]; then
  echo "[pre-commit] Running DocSync check..."
  if ! $PYBIN tools/doc_sync/cli.py check --strict; then
    echo "[pre-commit] DocSync check failed. Please run:"
    echo "  $PYBIN tools/doc_sync/cli.py write && git add ."
    echo "Then re-commit."
    exit 1
  fi
else
  echo "[pre-commit] DocSync CLI not found (tools/doc_sync/cli.py). Skipping."
fi

exit 0
