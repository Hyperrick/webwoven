#!/usr/bin/env sh
set -eu

if [ -n "${XDG_STATE_HOME:-}" ]; then
  state_home=$XDG_STATE_HOME
else
  state_home=${HOME:?HOME is required}/.local/state
fi

backup_dir=${BACKUP_DIR:-$state_home/webwoven/backups}
retention_days=${BACKUP_RETENTION_DAYS:-14}
database_service=${BACKUP_DATABASE_SERVICE:-postgres}
database_user=${BACKUP_DATABASE_USER:-webwoven}
database_name=${BACKUP_DATABASE_NAME:-webwoven}
archive_prefix=${BACKUP_ARCHIVE_PREFIX:-webwoven}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$backup_dir/$archive_prefix-$timestamp.sql.gz"

case "$retention_days" in
  "" | *[!0-9]*)
    echo "BACKUP_RETENTION_DAYS must be a non-negative integer." >&2
    exit 1
    ;;
esac
for value in "$database_service" "$database_user" "$database_name" "$archive_prefix"; do
  case "$value" in
    "" | *[!a-zA-Z0-9_-]*)
      echo "Backup service, database, user, and prefix must use safe identifier characters." >&2
      exit 1
      ;;
  esac
done

umask 077
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
docker compose exec -T "$database_service" \
  pg_dump -U "$database_user" -d "$database_name" | gzip -9 > "$archive"
find "$backup_dir" -type f -name "$archive_prefix-*.sql.gz" \
  -mtime "+$retention_days" -delete
echo "$archive"
