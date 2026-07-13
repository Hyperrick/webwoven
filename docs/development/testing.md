# Testing

The quality gate covers five layers:

1. Domain and property tests for scoring, navigation, hints, reachability, and state transitions.
2. Contract and repository tests for idempotency, stale versions, tokens, Daily, and reconnect.
3. Data-quality tests for referential integrity, licenses, shortest distances, and deterministic builds.
4. Content-gate regressions for schema limits, fact grounding, English dominance, answer leaks,
   provenance hashes, and editorial approval.
5. Browser tests for Solo, Daily, multiplayer, keyboard use, mobile layout, and reduced motion.

```sh
just check
```

Assisted content authoring and full remote snapshots are development workflows and never ordinary
CI steps. CI validates only committed, immutable artifacts and deterministic fixtures.
