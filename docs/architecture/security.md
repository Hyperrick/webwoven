# Security model

Webwoven treats the browser as an untrusted presentation client. The API owns time, legal moves,
hint selection, completion, score, and race order.

## Request boundaries

- A signed, `HttpOnly`, same-site cookie identifies a pseudonymous guest.
- State-changing browser requests require an accepted `Origin` and a constant-time CSRF match
  between the readable cookie, request header, and authenticated guest record.
- Each visible graph edge is represented by a short-lived HMAC token bound to the session, graph
  build, source node, edge, expected state version, and expiry.
- Session creation, room creation/readiness, commands, joins, starts, and content reports use
  action-specific pseudonymous rate limits that fail closed when shared storage is unavailable.
- WebSocket room messages never authorize a move; they transport room presence and progress only.
- WebSocket reconnects have both a fixed-window limit and a shared per-guest concurrency lease.
  Clients send functional keepalives, idle sockets close, and every connection has a maximum
  lifetime before a clean reconnect.

## Data boundaries

The Build Week release does not retain raw IP addresses or use third-party analytics. Its self-hosted
analytics adapter sets no cookie, honors Do Not Track, strips query strings and hashes, and accepts
only reviewed enum fields for five aggregate gameplay events. It never sends display names, guest,
session, or entity identifiers, free-form text, route histories, scores, or elapsed times. Umami
telemetry, public shares, heatmaps, and replay remain disabled, and detailed rows expire after 90
days. Display names are constrained and content reports are intentionally minimal. Secrets are
supplied at runtime and never enter images, client bundles, graph artifacts, or build logs.

## External systems

Wikidata and Commons are build-time data inputs only. Commons derivatives pass an automatic,
fail-closed license, provenance, raster, origin, and content-hash gate before entering the
immutable bundle. Codex-assisted prose and generated illustrations are created during development,
validated, manually approved, and compiled into immutable artifacts. Runtime containers receive
only the graph and accepted content; they have no AI integration or AI credentials and make no
Wikimedia request.

The credential-free base Compose stack binds its published ports to loopback. Public deployment
uses the production override, which refuses non-HTTPS origins, insecure cookies, placeholder or
reused signing keys, a placeholder database password, and an unverified graph directory. The
threat model is reviewed again before public deployment, especially proxy headers, edge-level
denial-of-service controls, and room-code enumeration.
