#!/usr/bin/env sh
set -eu

retention_days=${ANALYTICS_RETENTION_DAYS:-90}
case "$retention_days" in
  "" | *[!0-9]*)
    echo "ANALYTICS_RETENTION_DAYS must be a non-negative integer." >&2
    exit 1
    ;;
esac

docker compose exec -T analytics-db psql \
  -v ON_ERROR_STOP=1 \
  -v retention_days="$retention_days" \
  -U umami \
  -d umami <<'SQL'
BEGIN;
DELETE FROM event_data
WHERE created_at < now() - (:'retention_days' || ' days')::interval;
DELETE FROM session_data
WHERE created_at < now() - (:'retention_days' || ' days')::interval;
DELETE FROM revenue
WHERE created_at < now() - (:'retention_days' || ' days')::interval;
DELETE FROM session_replay
WHERE created_at < now() - (:'retention_days' || ' days')::interval;
DELETE FROM website_event
WHERE created_at < now() - (:'retention_days' || ' days')::interval;
DELETE FROM session
WHERE created_at < now() - (:'retention_days' || ' days')::interval;
COMMIT;
SQL

echo "analytics retention applied ($retention_days days)"
