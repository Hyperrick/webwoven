FROM ghcr.io/astral-sh/uv:0.11.24 AS uv

FROM python:3.13-slim
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/api services/api
COPY services/pipeline services/pipeline
COPY data/manifests/codex-content-artifact.schema.json data/manifests/
RUN uv sync --frozen --no-dev --package webwoven-pipeline
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["webwoven-pipeline"]
