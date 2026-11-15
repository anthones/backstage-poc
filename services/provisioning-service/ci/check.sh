#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Check committed files; never regenerate metadata or API snapshots in CI.
exec "${PYTHON:-python3}" -m pytest
