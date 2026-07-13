# Architecture

Webwoven is split by responsibility:

- The Svelte client renders the game and sends versioned commands.
- FastAPI owns guest identity, sessions, scoring, Daily, and room contracts.
- PostgreSQL stores durable application state.
- Valkey stores short-lived race state, streams, reconnect data, and rate limits.
- The pipeline fetches and normalizes open data, generates rounds, and compiles immutable graphs.
- Caddy serves the web client and documentation and proxies same-origin API traffic.

The runtime graph is an indexed, read-only SQLite bundle behind a `GraphReader` interface. The
interface permits a later CSR implementation without changing game rules or HTTP contracts.

No runtime process queries Wikidata, Wikimedia Commons, or an AI service. A session pins its graph,
round-generator, scoring, and content versions so it can be replayed exactly.
