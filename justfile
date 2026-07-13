set dotenv-load := true

install:
    corepack pnpm install
    uv sync --all-packages --group dev

dev-infra:
    docker compose up -d postgres valkey

dev-api:
    uv run --package webwoven-api uvicorn webwoven_api.main:create_app --factory --reload

dev-web:
    pnpm --filter @webwoven/web dev

fixture:
    uv run --package webwoven-pipeline webwoven-pipeline build-smoke

openapi:
    uv run python scripts/export_openapi.py

check:
    pnpm lint
    pnpm check
    pnpm test
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest
    uv run mkdocs build --strict
