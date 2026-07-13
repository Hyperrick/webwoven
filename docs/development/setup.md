# Local setup

## Requirements

- Node 24 or newer and Corepack
- Python 3.13 and uv
- Docker with Compose

## Start

```sh
cp .env.example .env
corepack pnpm install
uv sync --all-packages --group dev
docker compose up -d postgres valkey
uv run --package webwoven-api uvicorn webwoven_api.main:create_app --factory --reload
pnpm dev
```

Before starting either the split development servers or Compose, build and activate a real
Wikidata pack using the commands in [Data pipeline](../data/pipeline.md). The default graph path is
`data/builds/current/graph.sqlite3`; a missing real pack fails visibly instead of activating demo
data. `VITE_API_MODE=demo` exists only for isolated browser tests.

Replace the example signing secrets locally. The application and its Compose stack are completely
independent of AI credentials; approved Codex-assisted content is ordinary versioned
data in the build.

For the complete credential-free stack after the data build, run `docker compose up -d --build` and open
`http://localhost`. Compose uses its same-origin Caddy address independently of the `:5173` and
`:8000` origins used by the split Vite/API development workflow above.
