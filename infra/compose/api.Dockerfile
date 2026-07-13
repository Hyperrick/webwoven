FROM ghcr.io/astral-sh/uv:0.11.24 AS uv

FROM python:3.13-slim AS builder
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/api services/api
COPY services/pipeline services/pipeline
RUN uv sync --frozen --no-dev --package webwoven-api

FROM python:3.13-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/services/api /app/services/api
EXPOSE 8000
CMD ["uvicorn", "webwoven_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*", "--ws-max-size", "65536"]
