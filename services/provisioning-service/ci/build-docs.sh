#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# The generated artifact stays inside the owning repository.
exec "${PYTHON:-python3}" -m mkdocs build --strict --clean -f mkdocs.yml -d site
