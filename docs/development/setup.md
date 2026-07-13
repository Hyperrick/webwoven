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
uv run --package webwoven-pipeline webwoven-pipeline build-smoke
uv run --package webwoven-api uvicorn webwoven_api.main:app --reload
pnpm dev
```

Replace the example signing secrets locally. The application and its Compose stack are completely
independent of AI credentials; approved Codex-assisted content is ordinary versioned
data in the build.
