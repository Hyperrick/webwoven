# ADR 0002: Navigable route atlas

## Status

Accepted on 2026-07-14; amended on 2026-07-17.

## Context

Replacing the visible map after every move made route history difficult to understand and inspect.
Keeping inverse Wikidata relationships playable also allowed trivial two-node and longer cycles.
Both problems cross the navigation domain, session snapshots, API presentation, web interaction,
and decorative rendering, so they require one explicit ownership model rather than adapter-specific
fixes.

The canonical widening atlas also becomes unreadably small when fitted into a phone viewport.
Adapting its progression consistently crosses board presentation, camera following, semantic DOM
anchors, and decorative rendering without changing the underlying route or command contract.

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

The canonical `MapBoard` remains the deterministic semantic layout derived from the session
snapshot. At phone widths, a pure presentation projection remaps node coordinates and board bounds
into a top-to-bottom flow and packs each active frontier into a compact two-column constellation.
The current entity remains the only full card; history and the distant goal become compact labelled
markers. Occurrence identities, roles, links, choices, command tokens, and stage progression remain
unchanged.

Selecting a phone choice marker for the first time is ephemeral presentation state. It highlights
that choice, opens one detail tray, and exposes a small action indicator beside the selected marker,
but does not submit a command or spend a move. Activating the same selected marker again confirms
the choice through the same existing command path as the explicit tray action. Activating a
different marker switches the preview without moving. Desktop and tablet retain their full
direct-move cards. Semantic DOM controls and the Three.js/SVG adapters consume the same selected
presentation board.
The camera follows new stages on the horizontal axis for the canonical atlas and the vertical axis
for the phone projection; breakpoint changes refit the active bounds. CSS does not own graph
geometry or gameplay state.

## Consequences

- Refresh and reconnect reconstruct the same explored atlas without persisting browser command
  tokens.
- Players can inspect abandoned branches, zoom out, and return to the active stage without changing
  game state.
- Inverse knowledge remains available after a deliberate Back while accidental route loops are
  rejected server-side.
- Camera, board construction, navigation, presentation, and rendering stay independently testable.
- Phone layouts remain readable without changing the authoritative graph or command contract;
  first activation remains a preview, while either the tray action or repeated activation of the
  selected marker deliberately confirms the same command.
- DOM hit targets, graph lines, and decorative tokens remain aligned because every adapter consumes
  one presentation projection.
- Desktop and tablet retain the canonical widening atlas and direct cards, while viewport changes
  affect presentation geometry and camera bounds only.
- Runtime gameplay remains offline with respect to Wikidata, Commons, and AI providers.
