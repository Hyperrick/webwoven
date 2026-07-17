# Game rules

## Route Race

The player receives a start entity, target entity, and par distance. Selecting a neighboring
entity follows one stored relationship and counts as a move. Back returns to the previous
navigation node and also counts as a move.

Before a new round, Solo players confirm Easy, Normal, or Hard; relay hosts make the same locked
choice while creating the room. The last choice is remembered for convenience, but every new Solo
round requires confirmation. Daily difficulty remains part of its curated assignment. The server
selects unseen eligible rounds within a per-player cycle and avoids an immediate repeat whenever
more than one eligible route exists.

The data pipeline owns choice-first publication: every generated candidate must start with at least
two distinct playable targets, with parallel facts to the same target counted once. Automatic Solo,
Relay-room, and new Daily assignment pools verify that invariant again before selection. Explicit
round IDs and already-pinned Daily assignments remain available for deterministic replay.

Every mode reveals its category, difficulty, start, and goal during a five-second introduction that
ends at the server-owned `started_at` timestamp. The category remains visible above the start and
goal cards while the endpoints are revealed. Relay participants share exactly one timestamp.
Movement is unavailable before it, and elapsed play time begins from it. Reduced motion or missing
WebGL changes the presentation, not the duration or control boundary.

## Active-round interface

An active round begins with a compact **Round active** HUD for the timer, mode, difficulty, move
count, par, score, and Back command. The map board is the primary play surface: it marks the current
entity, shows exactly one visible goal marker, and places the immediately reachable entities
between them. It behaves as an expanding atlas rather than replacing one diagram with another.
On short phones at or below both 32rem wide and 42rem tall, the inner-route header compresses to
3rem and the active HUD becomes one row. **Live**, Time, Moves, Par, and Score remain visible, while
the complete round-status and mode text remains available to assistive technology. Back and header
controls retain 44px touch targets. The height recovered from those interface bands belongs to the
game canvas rather than leaving the graph crowded below stacked chrome. During an ordinary choice,
the map header also collapses to one visible **Your move** line and keeps **Where do you go next?**
as its accessible section heading. Compass selection and exhausted-branch headings remain fully
visible because their instructions cannot be reduced to that fallback.
Every Follow or Back command freezes the current decision stage. On desktop and tablet, the next
stage opens in a column to its right; on phones, it opens below in a vertical flow whose active
choices form a compact two-column constellation. The selected entity joins the visible breadcrumb
route; the alternatives remain on the map as muted, inspectable branches. The spatial canvas expands
with every resolved stage and automatically pans the newest playable stage into view. Back instead
fades the departed node into a muted history state and recenters the returned current node, reading
as the reverse of forward progress. Repeated entities remain separate visit occurrences, so a
retraced route never collapses the history into one dot.

The expanding atlas is a free spatial canvas rather than a one-directional strip. Players can drag
the background to pan in both directions, pinch or scroll around a pointer to zoom, fit the entire
explored map, or return to the current position. Arrow keys pan when the canvas is focused; `+` and
`-` zoom, `0` fits the map, and `Home` returns to the current node. A newly resolved move preserves
the player's zoom. Desktop and tablet pan the newest current stage into the left third of the
viewport, leaving the new frontier visible to its right; phones place it toward the upper portion,
leaving the new frontier visible below. The camera and decorative renderer move together over 320ms;
reduced-motion mode updates immediately. Hint-only updates do not pull the camera away from an older
branch being inspected. On phones, the current card, compact constellation, and selected detail tray
take containment priority so every route remains tappable without fitting several full cards into
the canvas.

Every earlier breadcrumb and muted alternative remains a focusable inspection point. Opening one
does not move the player or spend a command: it shows the entity description, whether the route was
taken, its documentary image, its source and target, and every stored fact for that connection.
The one exception is the immediately previous active-route node, which is also an inline Back
control on both pointer and touch layouts. Its first activation arms a visible Back indicator but
does not submit a command; activating the same node again sends the existing server-owned Back
command. Activating any other node clears that pending confirmation and preserves the ordinary
inspection behavior. The HUD Back control and `B` shortcut remain available.
When the acquired data includes a preferred Wikipedia sitelink, the inspector offers that external
article in a new tab; article text is never copied into the game bundle. These details are rebuilt
from the server-owned decision history after refresh or reconnect. Back stages suppress a duplicate
inverse option for the node they returned to, while the immutable visible trail still records the
Back action.

When the active branch has no playable connections, the map shows a non-modal recovery callout next
to the current node. Its primary action names the server-owned Back destination, states that Back
costs one move, and exposes the `B` shortcut. The previous active-route node retains its two-step
inline Back behavior; all other historical nodes remain inspection controls. The recovery action is
omitted at a start-node dead end and after the round leaves the active state.

On desktop and tablet, each reachable entity is a direct move card. It shows the entity name and the
complete stored fact sentence that justifies the connection; raw property labels are supporting
metadata, not the player's main instruction. The card orders a color-coded relationship glyph, the
fact sentence, and a square documentary image. On phones, the same choice is a compact labelled
bubble. Selecting that bubble for the first time only previews the route: it highlights the choice,
opens one detail tray containing the complete fact, artwork, and an explicit Move or Check action,
and exposes a small action indicator beside the selected bubble. Selecting that same bubble again
confirms through the same existing command as the tray action. Selecting a different bubble switches
the preview without spending a move or submitting a command.

For every ordinary connection, the graph line terminates directly at its semantic control without a
duplicate choice token, sequence number, or repeated action label. A reachable goal retains its
Ochre marker; on phones it uses the same compact preview and exposes an explicit Finish action in the
detail tray. Repeating activation on the selected goal bubble confirms the same Finish command.
Multiple semantic edges to the same entity are grouped into one move; all facts remain attached
while the deterministic primary fact is shown. Forward connections never offer an entity already
present in the active navigation route.

The raw knowledge graph deliberately retains useful inverse relationships, but the server removes
active-route targets before ranking the playable frontier, issuing command tokens, or calculating
hints. It also rejects a cyclic target if a client attempts to submit one directly. Back pops the
active route and is therefore the only way to retrace a path; after retracing, the abandoned branch
may be chosen again. This prevents two-node and longer navigation loops without permanently locking
a player out after a mistaken choice or deleting valid knowledge from the shared graph. Dense real
entities may have dozens of Wikidata neighbors, so the server projects at most six distinct
destinations into the current board. The projection is deterministic, rotates
across relationship types, and retains a distance-reducing edge whenever one remains route-safe. A
branch can still end when every remaining edge would repeat the active route or when the underlying
graph has no playable continuation; in that case the contextual Back recovery applies. The board
layout uses fixed deterministic 26rem columns and vertical lanes derived from the session snapshot,
so the same graph state produces the same positions without a hand-authored scene. Vertical lane
spacing adapts gently to frontier density: one or two lanes receive 11rem of breathing room, each
additional lane removes 0.5rem, and six or more lanes retain a 9rem minimum gap. A distant goal
marker receives a wider 52rem terminal gap from the active frontier, while a goal that becomes an
immediate move joins the ordinary choice column. The camera and Fit Map bounds use that same layout
geometry. The current card docks its right edge over the current token, and the distant-goal card
mirrors that treatment from its left edge. Each card masks half of its token so routes visually leave
the current entity and enter the destination through one shared anchor. Only the rightmost frontier
contains command tokens or move controls. Historical columns contain semantic entity and
relationship summaries with read-only inspection controls.

On phone-width screens, the same deterministic board is projected into a top-to-bottom flow instead
of shrinking the horizontal atlas. The current entity is the only full card. Compact history labels
remain above it, active choices occupy at most two columns below it, and the distant goal remains a
compact labelled marker beyond the frontier. One or two choices receive more breathing room; larger
frontiers add rows without stacking six full cards down the canvas. A reachable goal joins the same
compact choice constellation and reveals its Finish action in the detail tray and beside the
selected bubble. The first activation previews any compact choice; a second activation of that same
choice confirms it, while activating another choice switches the preview without moving. Crossing
the phone breakpoint clears ephemeral preview state, selects the appropriate card or constellation
presentation, and refits the active stage. Node identities, links, commands, scoring, and the desktop
and tablet board geometry do not change; desktop and tablet continue to use direct full cards. After
a phone move, camera fitting includes the immediately previous node alongside the current entity and
active frontier so the inline Back target remains reachable.

Before presenting a frontier with only one distinct destination, the server follows that forced
continuation through the stored graph. If it reaches neither the round target nor a node with at
least two route-safe destinations, the current node is treated as exhausted. This stops the player
at the entrance to a terminal corridor, so one Back returns to the genuine decision node instead of
inviting repeated moves into the same dead end. Direct one-move dead ends remain valid choices when
they are presented alongside real alternatives.

The timer is visually prominent but is not a live region, preventing screen readers from
announcing every second. Interactive nodes remain semantic DOM controls with full labels and fact
sentences; the map rendering is decorative and may disappear without removing a playable move.
Operating-system increased-contrast and forced-color preferences strengthen native controls
automatically; there is no separate in-game contrast mode.

The decorative Three.js layer uses raised, low-poly atlas tokens with discrete cel-shaded bands,
ink outlines, and physical shadows; it never owns input or game rules. If WebGL is unavailable, a
deterministic SVG fallback still shows the same nodes, depth cues, links, and discarded states. The
immutable result trail retains the complete relationship explanation for every move. Its
documentary artwork uses a centered contain treatment in a 5:4 frame, backed by a soft full-frame
version of the same image.

## Score

Let `d*` be the known shortest distance, `m` the moves used, `t` elapsed seconds, `T` the
difficulty time window, and `p` hint penalties.

```text
efficiency = d* / max(m, d*)
speed      = max(0, 1 - t / T)
score      = clamp(round(1000 × (0.80 × efficiency + 0.20 × speed)) - p, 0, 1000)
```

Difficulty windows are 120, 180, and 240 seconds for easy, normal, and hard.

## Hints

- **Compass** arms route-selection mode. The player then selects a visible route to evaluate that
  relationship group without moving, costing 75 points.
- **Lens** marks a relationship group on a near-optimal route, costing 150 points.
- **Map Fragment** reveals a valid future bridge entity, costing 250 points.

Selection is graph-derived. Generated language may describe a hint, but it never chooses one.
Hint feedback uses plain language and never exposes raw property IDs as player instructions.
On desktop and tablet, route count and map help share the compact map header with the move prompt. A
narrow rail on the map's right keeps zoom, Fit map, and Current at the top, then distributes the
three hint tools in a compact stack below a short divider. Hint explanations open inward on hover or
keyboard focus while the score penalty remains visible. The rail uses icon-only navigation and no
persistent panel or button outlines. Floating hint feedback never intercepts map input, and the node
canvas contains no persistent visible controls. Phone layouts keep the compact canvas toolbar and
horizontal hint dock.

## Live Relay

Two to four players receive the same round. Opponents see move count, hint use, and a coarse
progress band—not current nodes or routes. The first valid server-recorded finish wins; moves,
hints, and server time break near-simultaneous ties.
