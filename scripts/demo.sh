#!/usr/bin/env bash
set -euo pipefail
action="${1:-happy}"
activation() {
  curl --fail-with-body -sS -X POST http://localhost:8086/v1/activations \
    -H 'Content-Type: application/json' -H "X-Request-ID: demo-${action}" \
    -d "{\"tenant_id\":\"$1\"}" | python3 -m json.tool
}
fault() {
  curl --fail-with-body -sS -X POST http://localhost:8083/demo/fault \
    -H 'Content-Type: application/json' -d "{\"enabled\":$1}" | python3 -m json.tool
}
case "$action" in
  happy) activation tenant-acme ;;
  suspended) activation tenant-suspended ;;
  missing) activation tenant-missing ;;
  outage) fault true; activation tenant-acme ;;
  recover) fault false; activation tenant-acme ;;
  *) printf 'Usage: %s {happy|outage|recover|suspended|missing}\n' "$0" >&2; exit 2 ;;
esac
