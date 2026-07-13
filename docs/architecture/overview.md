# Architecture

Webwoven is split by responsibility:

- The Svelte client renders the game and sends versioned commands.
- A pure `MapBoard` domain projection turns each session snapshot into nodes, links, direct move
  choices, and normalized positions. Its output depends on semantic graph data, not signed edge
  tokens, animation timing, or browser state.
- A presentation-only Three.js renderer draws the paper field, paths, and markers. It does not own
  navigation, validate moves, or send commands.
- Entity choices remain accessible DOM buttons with complete fact sentences. The renderer is
  hidden from assistive technology. A deterministic SVG projection preserves visible nodes and
  links when WebGL is unavailable, and the same controls remain fully playable.
- FastAPI owns guest identity, sessions, scoring, Daily, and room contracts.
- PostgreSQL stores durable application state.
- Valkey stores short-lived race state, streams, reconnect data, and rate limits.
- The pipeline fetches and normalizes open data, generates rounds, and compiles immutable graphs.
- Caddy serves the web client and documentation and proxies same-origin API traffic.

The runtime graph is an indexed, read-only SQLite bundle behind a `GraphReader` interface. The
interface permits a later CSR implementation without changing game rules or HTTP contracts.

No runtime process queries Wikidata, Wikimedia Commons, or an AI service, and production performs
no AI calls. A session pins its graph, round-generator, scoring, and content versions so it can be
replayed exactly.
