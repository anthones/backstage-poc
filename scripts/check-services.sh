#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHON="$PWD/.venv/bin/python"
for service_dir in services/*-service; do
  printf '\nChecking %s\n' "$service_dir"
  "$service_dir/ci/check.sh"
done
node scripts/check-catalog.cjs
node --test scripts/check-techdocs-visibility.cjs
"$PYTHON" -m pytest scripts/test_demo_extensions.py -q
