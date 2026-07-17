# Deployment

Production uses Caddy, FastAPI, PostgreSQL, and Valkey under Docker Compose. The compiled Svelte
client and MkDocs site are copied into the Caddy image. The pipeline is build-time-only and has no
production credentials.

The base `docker-compose.yml` is a credential-free local stack and binds ports 80 and 443 to
`127.0.0.1`. It must not be used by itself as a public deployment definition. Public deployments
layer `docker-compose.production.yml` on top.

Caddy serves `/docs/` before the SPA fallback, proxies `/api/`, and upgrades the room WebSocket.
The graph bundle is downloaded from a versioned release and verified against its SHA-256 manifest
before the API is restarted.

The Build Week target is a small Hetzner EU server with a temporary IP-based TLS hostname. Server
creation and billable resources require explicit cost confirmation at deployment time.

## Production configuration

Copy `.env.production.example` to `.env` and replace every placeholder with an unquoted value.
Generate URL-safe secrets, for example with `openssl rand -hex 32`. The browser origin, API origin,
and Caddy site address must all use HTTPS; the separate redirect address must name the non-canonical
HTTPS host; the session and edge secrets must be different; secure cookies must be enabled; and
`WEBWOVEN_GRAPH_DIR` must name an existing, checksum-verified bundle. Caddy permanently redirects
the redirect address to the canonical site while preserving the request path and query string.

`infra/scripts/deploy.sh` validates these invariants without printing secrets, validates the merged
Compose model, and then deploys with both Compose files. The production override publishes ports
publicly and disables the demo graph fallback. A plain `docker compose up` remains local-only.

Database backups default outside the repository under the user's XDG state directory. The backup
script applies `umask 077`, creates a mode-700 directory, and keeps 14 days by default. If
`BACKUP_DIR` is intentionally set inside the checkout, `backups/` remains ignored by Git and the
Docker build context.
