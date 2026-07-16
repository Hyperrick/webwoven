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

## Know which app you are testing

| Name used in verification | URL                     | What is running                                                                            |
| ------------------------- | ----------------------- | ------------------------------------------------------------------------------------------ |
| **Compose acceptance**    | `http://localhost`      | Production-built web assets served by Caddy, the real API, and the active Wikidata pack.   |
| **Split development**     | `http://localhost:5173` | Vite hot-module reload, proxying API requests to the separately started server on `:8000`. |
| **Playwright isolation**  | `http://127.0.0.1:4173` | A disposable `VITE_API_MODE=demo` server started by the Playwright configuration.          |
| **API only**              | `http://localhost:8000` | FastAPI without the browser client.                                                        |

Manual acceptance uses **Compose acceptance** unless a test explicitly says otherwise. After a web
change, rebuild that surface with `docker compose build caddy && docker compose up -d caddy`, reload
the browser tab, and include `Surface: Compose acceptance (http://localhost)` in the verification
note. Use `:5173` for fast implementation feedback and `:4173` only for automated tests; neither is
evidence that the compiled Compose bundle was refreshed.

## Test from another device

`localhost` always means the device that opens the URL. To test from a phone on the same trusted
Wi-Fi network, find the Mac's LAN address with `ipconfig getifaddr en0`, then set these local `.env`
values before recreating the API and Caddy services:

```dotenv
WEBWOVEN_BIND_ADDRESS=0.0.0.0
WEBWOVEN_COMPOSE_ORIGIN=http://192.168.x.x
WEBWOVEN_COMPOSE_API_ORIGIN=http://localhost
WEBWOVEN_SITE_ADDRESS=:80
```

Open `http://192.168.x.x` on the phone. The second allowed origin keeps desktop testing at
`http://localhost` working. Binding to `0.0.0.0` makes the development server reachable by other
devices on the local network, so return `WEBWOVEN_BIND_ADDRESS` to `127.0.0.1` on untrusted networks.
