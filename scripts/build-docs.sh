#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHON="$PWD/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  printf 'Run ./scripts/setup.sh first.\n' >&2
  exit 1
fi
for service_dir in services/*-service; do
  # Same verification-before-docs order as repository CI. Sources stay untouched.
  (cd "$service_dir" && "$PYTHON" -m pytest tests/test_contract.py)
  "$service_dir/ci/build-docs.sh"
done
"$PYTHON" scripts/publish-docs.py
