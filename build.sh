#!/usr/bin/env bash
# this_file: build.sh
# Build only the adjacent documentation: ./build.sh --docs [renderer options]
if [[ "${1:-}" == --docs ]]; then
  shift
  set -euo pipefail
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
  export PYTHONPATH="$PWD:$PWD/src:$PWD/../src:$PWD/..${PYTHONPATH:+:$PYTHONPATH}"
  exec uvx --python 3.12 --from mkdocs==1.6.1 \
    --with mkdocs-material \
    --with 'mkdocstrings[python]' \
    --with mkdocs-git-revision-date-localized-plugin \
    --with pymdown-extensions \
    mkdocs build --config-file mkdocs.yml "$@"
fi

# build.sh: Lint, test, and build opero
# opero: Resilient, parallel task orchestration for Python

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Linting ==="
uvx ruff check --fix --unsafe-fixes . || true
uvx ruff format . || true

echo "=== Tests ==="
if [ -d "tests" ] || find . -name "test_*.py" -not -path "./.git/*" | grep -q .; then
    python -m pytest -x || true
else
    echo "No tests found, skipping."
fi

echo "=== Build ==="
uvx hatch build

echo "=== Build complete ==="
