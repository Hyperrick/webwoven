# Architecture

Webwoven is split by responsibility:

- The Svelte client renders the game and sends versioned commands.
- The session domain freezes one token-free decision frame for every applied Follow or Back
  command. A frame records the exact visible frontier, selected edge when applicable, source,
  destination, and action. Hints, stale commands, and duplicate idempotency keys do not append a
  frame. Persisted frames make the exploration map identical after GET, refresh, or reconnect.
- A pure `MapBoard` domain projection turns the current frontier and resolved decision frames into
  occurrence-scoped nodes, links, direct move choices, deterministic columns, and normalized
  positions. Each move grows the world width while earlier column assignments and horizontal world
  positions stay fixed; vertical normalization may adjust when a later stage needs more lanes. Only
  the active frontier consumes signed edge tokens; stored history is semantic and token-free.
- A presentation-only Three.js renderer draws the paper field, paths, and cel-shaded atlas tokens.
  It does not own navigation, validate moves, or send commands.
- A pure map-camera module owns pan, cursor-anchored zoom, fit, focus, visibility bounds, and zoom
  limits. One camera state drives the transformed semantic DOM world and the Three.js/SVG adapters,
  so decorative markers never drift away from their interactive controls. WebGL keeps a
  viewport-sized drawing buffer and changes only its orthographic projection while panning or
  zooming; the ever-widening scene is not rendered into an ever-widening framebuffer.
- Entity choices remain accessible DOM buttons with complete fact sentences. The renderer is
  hidden from assistive technology. A deterministic SVG projection preserves visible nodes and
  links when WebGL is unavailable, and the same controls remain fully playable. Historical entity
  buttons open a read-only inspection projection of token-free decision facts and never issue a
  move command.
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

Normal development and production also fail closed on graph loading. They require the configured
immutable SQLite bundle; only the explicit `testing` environment may construct the in-memory test
graph, and browser demo data requires the test-only `VITE_API_MODE=demo` flag.
