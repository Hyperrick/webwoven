# ADR 0003: Synchronized round introduction and varied selection

## Status

Accepted on 2026-07-15.

## Context

Solo and relay creation previously selected the first eligible published round, so repeated plays
could return the same route indefinitely. Relay alone had a short room countdown, while Solo and
Daily exposed the playable board immediately. That made category artwork, endpoints, timing, and
control availability inconsistent across modes.

## Decision

Every newly created session receives an absolute `started_at` five seconds in the future. Relay
creates every participant session with the room's one shared countdown timestamp. The API rejects
all commands before that instant. Clients derive the introduction phase and elapsed play time from
the timestamp rather than a local countdown, so late responses advance and resumed sessions at or
after the start skip the introduction.

One shared web introduction reveals category and difficulty, separates the start and goal along a
thread, returns orientation to the start, and match-zooms into play. Accessible DOM owns the text;
the dynamically loaded Three.js scene is decorative and disposable. Reduced motion and failed
WebGL use the same timestamp with a static composition. Reviewed category plates are served from
the existing approved illustration manifest; entity art is optional.

Solo players and relay hosts confirm Easy, Normal, or Hard before creation. Daily remains curated.
One history-aware selector filters by category and difficulty, chooses unseen rounds within a
cycle, and excludes the immediately prior round when a new cycle begins and another candidate
exists. Explicit round IDs and Daily assignments remain deterministic bypasses.

## Consequences

- Controls, scoring time, and relay fairness share one server-owned boundary.
- Category and endpoint presentation is consistent in Solo, Daily, and Relay without making the
  decorative scene authoritative.
- PostgreSQL and memory adapters retain per-player selection history for the active graph and
  filter, while an injected chooser keeps domain tests deterministic.
- Session and room snapshots carry enough category, difficulty, artwork, endpoint, and timing data
  for reconnect-safe presentation.
- A new selection-history table is created by the existing schema lifecycle in production.
