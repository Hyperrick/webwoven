# Midpoint system map

Webwoven is live at [www.webwoven.org](https://www.webwoven.org) halfway through Build Week. The
deployed product already includes Single player, Daily challenge, synchronized Multiplayer,
responsive route exploration, source inspection, and privacy-minimized aggregate reporting. The
remaining release work is verification and presentation rather than a change to the core runtime
architecture.

![Webwoven production runtime and build-time atlas pipeline](../assets/architecture-midpoint.svg)

## Runtime boundary

The browser reaches one public Caddy edge. Caddy terminates TLS, serves the compiled Svelte client
and MkDocs site, redirects the apex domain to the canonical `www` host, and proxies API and room
traffic to FastAPI. FastAPI is the only owner of authoritative gameplay rules.

| Domain | Owner | State and dependencies |
| --- | --- | --- |
| Presentation | Svelte semantic controls plus a presentation-only Three.js/SVG map | Versioned API contracts; no game-rule ownership |
| Navigation and sessions | FastAPI session domain | Frozen decision frames, signed active choices, replayable versions |
| Graph access | `GraphReader` | Indexed, immutable SQLite atlas mounted read-only |
| Scoring and hints | Pure server domain services | Pinned rule versions and deterministic penalties |
| Multiplayer rooms | Room service | PostgreSQL durability plus Valkey streams, expiry, and reconnect state |
| Reporting | Small client allowlist plus self-hosted Umami | Cookie-free page views and five coarse events; never blocks gameplay |
| Edge and operations | Caddy and Compose deployment scripts | TLS, same-origin routing, health checks, backups, and retention |

A gameplay request never reaches Wikidata, Wikimedia Commons, Wikipedia, or an AI service. All
entity facts, links, and licensed images are served from the reviewed release bundle. A session pins
its graph, content, route-generator, and scoring versions so a recorded route can be reproduced.

## Build-time knowledge pipeline

The Python pipeline is deliberately outside the production request path:

1. Versioned Wikidata and Commons inputs are acquired and checksummed.
2. Entities, readable relation directions, source ranks, article links, and media licenses are
   normalized into owned domain records.
3. Candidate routes are generated and rejected unless they satisfy graph, choice, content, media,
   and policy checks.
4. Approved records compile into an immutable SQLite graph, local media directory, manifest, and
   attribution ledger.
5. Deployment verifies the manifest checksum before activating a release.

Codex can assist with build artifacts and documentation, but those artifacts are reviewed and
labelled at build time. Codex is not a production dependency and does not decide moves, scores,
routes, or winners.

## Production topology

The current Hetzner deployment runs the public edge, API, application PostgreSQL, Valkey, Umami,
and a separate analytics PostgreSQL service under Docker Compose. Umami's direct port is bound to
loopback; only Caddy publishes the dashboard and tracker. Application and analytics databases are
backed up independently, and aggregate analytics rows have a 90-day retention job.

| Public address | Purpose |
| --- | --- |
| `https://www.webwoven.org` | Canonical game, API, privacy page, and documentation |
| `https://webwoven.org` | Permanent redirect to the canonical host |
| `https://stats.webwoven.org` | Self-hosted analytics tracker and private dashboard |

## Midpoint release snapshot

- 3,970 playable entities and 22,402 named directed relationships
- ten knowledge categories and 100 validated, published routes
- 3,621 locally served, attributed Commons source files
- Single player, shared Daily challenge, and two-to-four-player synchronized races
- desktop/tablet left-to-right atlas and phone top-to-bottom two-column constellation
- deterministic hints, scoring, Back behavior, reconnect, and replayable session versions

The midpoint quality gate passes 134 web unit tests, 347 Python tests, and 32 desktop/mobile browser
flows, alongside formatting, lint, type checking, strict documentation, data validation, and
container-build checks.

The final half focuses on accessibility, security and load verification, content review, demo
recording, and submission packaging. The detailed domain boundaries remain in the
[architecture overview](overview.md) and [responsibility map](../development/responsibility-map.md).
