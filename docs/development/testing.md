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
stage-follow panning, direct line-to-card endpoints, choice-token suppression, connection-to-goal
lane separation, contextual dead-end recovery, and narrow-phone containment.

Cycle regressions use a deliberately bidirectional graph. They verify that inverse edges remain in
the shared data bundle, targets already present in the active route disappear before frontier
ranking and hint selection, direct cyclic commands are rejected without mutation, and Back pops
the route so a deliberate retry becomes available again. The Albert Einstein → Czech Republic →
UNESCO → Austria real-data path is also exercised in a browser smoke check.

```sh
just check
```

Assisted content authoring and full remote snapshots are development workflows and never ordinary
CI steps. CI validates only committed, immutable artifacts and deterministic fixtures.
