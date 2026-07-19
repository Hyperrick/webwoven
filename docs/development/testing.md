# Testing

The quality gate covers five layers:

1. Domain and property tests for scoring, navigation, hints, reachability, and state transitions.
2. Contract and repository tests for idempotency, stale versions, tokens, Daily, and reconnect.
3. Data-quality tests for referential integrity, licenses, shortest distances, and deterministic builds.
4. Content-gate regressions for schema limits, fact grounding, English dominance, answer leaks,
   provenance hashes, and editorial approval.
5. Browser tests for Solo, Daily, multiplayer, keyboard use, mobile layout, and reduced motion.

The map-camera suite additionally locks cursor-anchored zoom, pinch translation, fit padding,
recoverable pan bounds, active-frontier visibility, and the renderer view contract. Map history
tests cover Follow and Back reconstruction after resume, grouped token-free fact preservation, and
duplicate return-node suppression. Real-browser canvas checks exercise background drag, zoom and
fit controls, historical inspection, WebGL/SVG alignment, current/goal token clearance, automatic
stage-follow panning, direct line-to-choice endpoints, choice-token suppression, contextual
dead-end recovery, and narrow-phone containment. Phone regressions additionally lock deterministic
two-column constellation packing, first-tap preview without a command, the selected marker's action
indicator, second-tap confirmation through the same command as the explicit detail-tray action,
preview switching without movement, compact reachable-goal handling, and refitting between phone
and desktop/tablet presentations. Desktop opening-stage coverage measures the complete start and
distant-goal cards against the actual map viewport after the endpoint reveal has closed, preventing
the intro-to-round camera transition from clipping either endpoint. Long-label coverage uses the
121-character longest published entity name at 320×568 and 390×844 to verify full natural wrapping
for history and route-preview labels, equal label-block heights within each two-node row, vertical
centering, adaptive projection spacing, and the absence of clipping, overlap, or ellipses. Desktop and phone
flows also verify that the immediately previous node is the sole inline Back target, the first
activation only arms its visible and accessible Back state, and the second activation submits the
same Back command while preserving route-history reconstruction. After a confirmed phone move, the
camera keeps that target, the current stage, and every newly available frontier node visible.
Exhausted-branch recovery additionally requires the complete returned current card to sit inside the
phone map viewport after Back, while desktop retains its stationary collapse camera.
Phone coverage at the 32rem vertical-map breakpoint verifies one unclipped HUD row with Time, Moves,
and the complete wrapping Target; Score, the map header, the canvas toolbar, and a disabled Back
action remain hidden. Available Back and the compact icon-plus-penalty hint controls retain at least
44px touch targets while the recovered height belongs to the node canvas. The initial current card
opens close beneath the HUD, and post-move fitting retains the inline Back target, current stage, and
complete frontier. Additional assertions lock the 40px visible choice pin inside its larger semantic
control, the 90% decorative token scale, complete row-equalized labels, and a centered multi-line
distant goal. Desktop and phone completion flows share the continuous reachable-goal heartbeat;
system and in-app reduced-motion coverage verifies its suppression.

Cycle regressions use a deliberately bidirectional graph. They verify that inverse edges remain in
the shared data bundle, targets already present in the active route disappear before frontier
ranking and hint selection, direct cyclic commands are rejected without mutation, and Back pops
the route so a deliberate retry becomes available again. The Albert Einstein → Czech Republic →
UNESCO → Austria real-data path is also exercised in a browser smoke check.
Frontier regressions separately cover one forced corridor, several immediate dead ends, several
longer terminal corridors, a branch whose children are all terminal, a corridor that reaches the
target, a direct dead end retained beside a genuine target-reaching alternative, and a route-safe
choice retained beyond the six-choice display cap.

Round-selection regressions cover forced-opening exclusion for Solo, multiplayer-lobby, and new Daily
assignments while preserving explicit and already-pinned replay. They also lock the four/four/two
published pool per category, unseen-route cycling, immediate-repeat avoidance, and history
continuity when a player changes category filters. The Solo completion browser flow verifies the
finite, pointer-transparent confetti layer without horizontal overflow and its suppression under
reduced motion. Pipeline regressions cover source
ordinals, canonical forward/inverse sentences, semantic `P166` and `P17` wording, the all-source
compiler guard, and hash-verified offline semantic refresh. The browser suite locks result-trail
artwork to a centered contain treatment inside its 5:4 frame.

```sh
just check
```

Assisted content authoring and full remote snapshots are development workflows and never ordinary
CI steps. CI validates only committed, immutable artifacts and deterministic fixtures.
