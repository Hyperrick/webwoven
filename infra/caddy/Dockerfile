FROM node:24-alpine AS web
ARG VITE_ANALYTICS_ORIGIN
ARG VITE_ANALYTICS_WEBSITE_ID
ARG VITE_ANALYTICS_DOMAIN
ENV VITE_ANALYTICS_ORIGIN=$VITE_ANALYTICS_ORIGIN \
    VITE_ANALYTICS_WEBSITE_ID=$VITE_ANALYTICS_WEBSITE_ID \
    VITE_ANALYTICS_DOMAIN=$VITE_ANALYTICS_DOMAIN
RUN corepack enable
WORKDIR /src
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/design-tokens/package.json packages/design-tokens/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web apps/web
COPY packages/design-tokens packages/design-tokens
RUN pnpm --filter @webwoven/web build

FROM python:3.13-slim AS docs
WORKDIR /src
RUN pip install --no-cache-dir mkdocs-material==9.7.6
COPY mkdocs.yml ./
COPY docs docs
RUN mkdocs build --strict

FROM caddy:2.10-alpine
COPY infra/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=web /src/apps/web/dist /srv/web
COPY --from=docs /src/site /srv/docs
