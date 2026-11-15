#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null
if [[ ! -x .venv/bin/python ]]; then
  "${PYTHON:-python3}" -m venv .venv
fi
.venv/bin/python -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12+ is required"'
.venv/bin/python -m pip install -r requirements.txt
(
  cd backstage
  node .yarn/releases/yarn-4.13.0.cjs install --immutable
)
./scripts/build-docs.sh
printf '\nReady. Run ./scripts/start.sh, then open http://localhost:3000/\n'
