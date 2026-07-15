# Webwoven

**Connect anything. Discover why it is connected.**

Webwoven is a competitive, explainable knowledge-graph game. Players move between real
people, places, events, works, species, and scientific ideas by following named relationships
rather than opaque hyperlinks.

The project is also an open Build Week case study for a simple belief:

> Everyone with an idea can become a game developer.

Codex is used to turn the product brief into a modular, tested game, validated educational
content, and a living public build journal. Gameplay, routes, scores, and winners remain
deterministic and server-authoritative.

## Build Week scope

- Solo Route Race
- Daily Connection and leaderboard
- Live Relay for two to four players with reconnect
- Four knowledge categories, with 100 candidates and 40 automatically validated production rounds
- Local, immutable Wikidata graph with licensed Commons media
- English desktop and mobile web experience

Normal gameplay now requires an immutable Wikidata bundle. The repository retains a clearly
labelled synthetic smoke fixture only for isolated automated tests; neither the browser nor the API
silently substitutes it when the real atlas is unavailable. The release-scale graph and licensed,
locally served Commons endpoint media are implemented; editorial content, the load target, and
public deployment remain dated milestones in the living documentation.

## Local development

Prerequisites: Node 24+, Corepack, Python 3.13, uv, and Docker.

```sh
corepack pnpm install
uv sync --all-packages --group dev
docker compose up -d postgres valkey
uv run --package webwoven-api uvicorn webwoven_api.main:create_app --factory --reload
pnpm dev
```

Build and activate the real Wikidata playtest pack first by following
[`docs/data/pipeline.md`](docs/data/pipeline.md). Copy `.env.example` to `.env` and replace local
signing secrets before starting the API. No AI account, key, or runtime service is required to
build, run, or play the game.
The local Compose ports bind to loopback. Public deployments must use the separately validated
production override described in `docs/operations/deployment.md`.

## Documentation

Run `uv run mkdocs serve` for the living documentation. Data provenance, architecture, rules,
AI boundaries, operations, and the Codex build log are maintained alongside the code.

## License

Source code and authored documentation are MIT licensed. Imported Wikidata data and Wikimedia
Commons assets retain their source licenses and are covered by build-specific attribution
manifests and `THIRD_PARTY_NOTICES.md`.
