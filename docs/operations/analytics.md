# Analytics operations

Webwoven hosts Umami 3.1.0 at `https://stats.webwoven.org`. The release pins the multi-platform image
digest and keeps PostgreSQL on an internal Compose network. Port 3000 is additionally bound to VPS
loopback so deployment bootstrap can run before the public proxy starts; it is never publicly
published.

## Privacy configuration

- no analytics cookies, identity calls, advertising profiles, or cross-site tracking;
- no query strings, URL hashes, guest/session/entity IDs, names, or free-form event values;
- Do Not Track prevents the tracker from loading;
- Umami telemetry, update checks, external calls, public sharing, heatmaps, and replay are disabled;
- detailed rows are removed after 90 days by `infra/scripts/prune-analytics.sh`;
- the public disclosure is available at `/privacy`.

The tracker reports automatic page views and the fixed events documented in ADR 0007. The adapter's
runtime allowlist drops properties that are not owned by the named event contract.

## Bootstrap and access

Production `.env` supplies a stable website UUID plus separate database, application, and dashboard
secrets. `infra/scripts/deploy.sh` starts the private analytics services first, rotates Umami's
default administrator password, creates or verifies the Webwoven website, explicitly disables
recording, and only then starts the public Caddy service. Secrets are never printed.

The dashboard login is `admin`; the password is the server-only `UMAMI_ADMIN_PASSWORD` value. The
dashboard must remain authenticated and must never enable a share URL or session recording.

## Retention and backups

Run retention daily from `/opt/webwoven/current`:

```sh
ANALYTICS_RETENTION_DAYS=90 sh infra/scripts/prune-analytics.sh
```

Back up the analytics database with the shared PostgreSQL backup runner:

```sh
BACKUP_DIR=/opt/webwoven/backups \
BACKUP_DATABASE_SERVICE=analytics-db \
BACKUP_DATABASE_USER=umami \
BACKUP_DATABASE_NAME=umami \
BACKUP_ARCHIVE_PREFIX=analytics \
sh infra/scripts/backup-postgres.sh
```

Restore testing must use an isolated database before any production incident requires it.
