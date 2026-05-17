#!/usr/bin/env bash
# install.sh: Install opero in editable mode
# opero: Resilient, parallel task orchestration for Python

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Installing opero (editable) ==="
uv pip install -e .
echo "=== Install complete ==="
