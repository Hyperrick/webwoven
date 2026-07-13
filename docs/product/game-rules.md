# Game rules

## Route Race

The player receives a start entity, target entity, and par distance. Selecting a neighboring
entity follows one stored relationship and counts as a move. Opening a relationship group is
free. Back returns to the previous navigation node and also counts as a move.

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

- **Compass** evaluates a player-selected relationship group, costing 75 points.
- **Lens** marks a relationship group on a near-optimal route, costing 150 points.
- **Map Fragment** reveals a valid future bridge entity, costing 250 points.

Selection is graph-derived. Generated language may describe a hint, but it never chooses one.

## Live Relay

Two to four players receive the same round. Opponents see move count, hint use, and a coarse
progress band—not current nodes or routes. The first valid server-recorded finish wins; moves,
hints, and server time break near-simultaneous ties.
