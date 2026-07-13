#!/usr/bin/env sh
set -eu

if [ -n "${XDG_STATE_HOME:-}" ]; then
  state_home=$XDG_STATE_HOME
else
  state_home=${HOME:?HOME is required}/.local/state
fi

backup_dir=${BACKUP_DIR:-$state_home/webwoven/backups}
retention_days=${BACKUP_RETENTION_DAYS:-14}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$backup_dir/webwoven-$timestamp.sql.gz"

case "$retention_days" in
  "" | *[!0-9]*)
    echo "BACKUP_RETENTION_DAYS must be a non-negative integer." >&2
    exit 1
    ;;
esac

umask 077
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
docker compose exec -T postgres pg_dump -U webwoven -d webwoven | gzip -9 > "$archive"
find "$backup_dir" -type f -name 'webwoven-*.sql.gz' -mtime "+$retention_days" -delete
echo "$archive"
