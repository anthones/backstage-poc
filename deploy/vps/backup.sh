#!/usr/bin/env bash
# Root-owned installed copy; see the VPS runbook for /etc/acmesecure/backup.env.
set -euo pipefail
umask 077
set -a
source /etc/acmesecure/backup.env
set +a
: "${RESTIC_REPOSITORY:?Configure an off-host repository}"
: "${RESTIC_PASSWORD_FILE:?Configure the repository password file}"
exec 9>/run/lock/acmesecure-backup.lock
flock -n 9
COMPOSE=/usr/local/sbin/acme-compose
"$COMPOSE" ps --status running --services | grep -qx backstage
stopped=no
resume_backstage() {
  local status=$?
  if [[ "$stopped" == yes ]]; then
    "$COMPOSE" start backstage || status=1
  fi
  exit "$status"
}
trap resume_backstage EXIT
stopped=yes
"$COMPOSE" stop backstage
"$COMPOSE" exec -T postgres pg_dumpall -U backstage > /var/backups/acmesecure/latest.sql.tmp
test -s /var/backups/acmesecure/latest.sql.tmp
mv /var/backups/acmesecure/latest.sql.tmp /var/backups/acmesecure/latest.sql
"$COMPOSE" start backstage
stopped=no
restic backup --tag acmesecure-vps \
  /var/backups/acmesecure/latest.sql \
  /etc/acmesecure /etc/caddy /usr/local/sbin/acme-compose \
  /usr/local/sbin/acme-backup /srv/acmesecure/releases
restic forget --tag acmesecure-vps --keep-daily 7 --keep-weekly 4 --prune
restic check
