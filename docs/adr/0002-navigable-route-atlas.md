# ADR 0002: Navigable route atlas

## Status

Accepted on 2026-07-14.

## Context

Replacing the visible map after every move made route history difficult to understand and inspect.
Keeping inverse Wikidata relationships playable also allowed trivial two-node and longer cycles.
Both problems cross the navigation domain, session snapshots, API presentation, web interaction,
and decorative rendering, so they require one explicit ownership model rather than adapter-specific
fixes.

## Decision

The navigation domain owns one cycle-free active route and one immutable visible trail. Following
an entity already present in the active route is invalid. Back is the only retrace command: it pops
the active route, appends the returned entity to the visible trail, and costs one move. The graph
bundle retains valid inverse knowledge; the session-owned playable-frontier projection removes
active-route targets before ranking, token issuance, command validation, and hint selection.

Every resolved frontier is pinned to the session as graph edge identifiers. API presentation emits
token-free historical choices with every grounded connection for each destination. Signed command
tokens remain exclusive to the current frontier.

The web client derives one deterministic, widening `MapBoard` from that snapshot. A pure camera
module owns pan, zoom, fit, focus, and visibility bounds. Semantic DOM buttons own all interaction
and accessibility; Three.js and SVG are decorative adapters that consume the same board and camera
contracts. Historical nodes open read-only inspection and never issue move commands.

## Consequences

- Refresh and reconnect reconstruct the same explored atlas without persisting browser command
  tokens.
- Players can inspect abandoned branches, zoom out, and return to the active stage without changing
  game state.
- Inverse knowledge remains available after a deliberate Back while accidental route loops are
  rejected server-side.
- Camera, board construction, navigation, presentation, and rendering stay independently testable.
- Runtime gameplay remains offline with respect to Wikidata, Commons, and AI providers.
