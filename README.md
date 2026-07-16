# Webwoven

**Connect anything. Discover why it is connected.**

Webwoven is a competitive, explainable knowledge-graph game. Players move between real people,
places, events, works, species, and scientific ideas by following named relationships—not opaque
hyperlinks. Every move answers both _where can I go?_ and _why are these things connected?_

![Webwoven frontispiece with Single player, Daily challenge, and Multiplayer modes](docs/assets/screenshots/frontispiece.webp)

The project is also an open Build Week case study for a simple belief:

> Everyone with an idea can become a game developer.

Codex turns the product brief into a modular, tested game, a validated knowledge atlas, and a
living public build journal. Gameplay, routes, scores, and winners remain deterministic and
server-authoritative.

## What you can play

- **Single player** — choose a difficulty and find a route at your own pace.
- **Daily challenge** — solve the same connection as everyone else and compare scores.
- **Multiplayer** — race a synchronized route live with two to four players, including reconnect.

A round reveals a start, a goal, category, difficulty, and known par. Each move follows one
documented graph relationship. Players can inspect the underlying fact, documentary image,
attribution, and preferred Wikipedia article without changing position. Efficient routes score
best; three deterministic hint tools trade points for guidance.

![A live Webwoven Solo map using the real Compose atlas](docs/assets/screenshots/solo-map.webp)

## The current atlas

- 3,970 playable Wikidata entities and 22,402 directed, named relationships
- ten readable knowledge categories
- 100 validated round candidates, including 40 published routes
- local, policy-checked Commons media for every entity through 3,621 attributed source files
- 3,778 preferred Wikipedia article links
- no Wikidata, Commons, Wikipedia, or AI request during gameplay

The synthetic smoke fixture is test-only. Normal gameplay requires an immutable real-data bundle
and fails visibly if one is unavailable.

## How it is built

| Layer                 | Responsibility                                                                   |
| --------------------- | -------------------------------------------------------------------------------- |
| Svelte 5 + TypeScript | Accessible game UI, responsive modes, and semantic controls                      |
| Three.js              | Decorative atlas paper, paths, and tokens; gameplay remains usable without WebGL |
| FastAPI               | Authoritative sessions, route projection, hints, scoring, Daily, and Relay rules |
| SQLite atlas          | Immutable compiled Wikidata entities, relationships, rounds, and media records   |
| PostgreSQL + Valkey   | Durable player state and low-latency multiplayer coordination                    |
| Python pipeline       | Versioned Wikidata acquisition, Commons licensing, validation, and compilation   |

Runtime boundaries keep the network, persistence, UI, and game domains separate. See the
[architecture overview](docs/architecture/overview.md) and
[responsibility map](docs/development/responsibility-map.md).

## Run locally

Prerequisites: Node 24+, Corepack, Python 3.13, uv, Docker, and Just.

Build and activate the real Wikidata playtest pack by following the
[data pipeline guide](docs/data/pipeline.md), then run the complete same-origin stack:

```sh
cp .env.example .env
just install
docker compose up -d --build
```

Open `http://localhost`. Replace the example signing secrets before sharing the stack beyond your
machine. No AI account, key, or runtime service is required to build or play Webwoven.

For hot-reload development, start the infrastructure, API, and Vite client separately:

```sh
just dev-infra
just dev-api
just dev-web
```

### Local test surfaces

| Surface              | URL                     | Data and purpose                                                                           |
| -------------------- | ----------------------- | ------------------------------------------------------------------------------------------ |
| Compose acceptance   | `http://localhost`      | Compiled Caddy client, real API, and active Wikidata pack. Canonical manual product check. |
| Split development    | `http://localhost:5173` | Vite hot reload against the separately running API on `:8000`.                             |
| Playwright isolation | `http://127.0.0.1:4173` | Temporary demo-mode server owned by `pnpm test:e2e`; automated tests only.                 |
| API only             | `http://localhost:8000` | FastAPI endpoints and health checks; no product UI.                                        |

Every verification note names its surface and URL. After frontend changes, rebuild Compose with
`docker compose build caddy && docker compose up -d caddy`, reload `http://localhost`, and verify
there before reporting acceptance. A `:4173` result never substitutes for the real-data stack.

## Quality gate

```sh
just check
pnpm test:e2e
```

The gate covers formatting, linting, type checking, Python and web tests, file-size limits, strict
documentation builds, desktop/mobile browser flows, deterministic data validation, and container
builds in CI.

## Documentation

- [Game rules](docs/product/game-rules.md)
- [Architecture](docs/architecture/overview.md)
- [Data pipeline and provenance](docs/data/pipeline.md)
- [Local setup and testing surfaces](docs/development/setup.md)
- [Build Week journal](docs/build-log/2026-07-16.md)
- [Deployment](docs/operations/deployment.md)

Run `uv run mkdocs serve` for the complete living documentation.

## License

Source code and authored documentation are MIT licensed. Imported Wikidata data and Wikimedia
Commons assets retain their source licenses and are covered by build-specific attribution
manifests and `THIRD_PARTY_NOTICES.md`. Screenshot-specific notices are recorded in
[`docs/assets/screenshots/README.md`](docs/assets/screenshots/README.md).
