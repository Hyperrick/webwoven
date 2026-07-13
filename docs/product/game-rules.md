# Game rules

## Route Race

The player receives a start entity, target entity, and par distance. Selecting a neighboring
entity follows one stored relationship and counts as a move. Back returns to the previous
navigation node and also counts as a move.

## Active-round interface

An active round begins with a compact **Round active** HUD for the timer, mode, difficulty, move
count, par, score, and Back command. The map board is the primary play surface: it marks the
current entity, shows exactly one visible goal marker, and places the immediately reachable
entities between them.

Each reachable entity is a direct move button. It shows the entity name and the complete stored
fact sentence that justifies the connection; raw property labels are supporting metadata, not the
player's main instruction. Multiple semantic edges to the same entity are grouped into one move;
all facts remain attached while the deterministic primary fact is shown. Selecting a button follows
that edge. The board layout uses fixed deterministic lanes derived from the session snapshot, so the
same graph state produces the same positions without a hand-authored scene.

The timer is visually prominent but is not a live region, preventing screen readers from
announcing every second. Interactive nodes remain semantic DOM controls with full labels and fact
sentences; the map rendering is decorative and may disappear without removing a playable move.
If WebGL is unavailable, a deterministic SVG fallback still shows the same nodes and links. The
immutable result trail retains the complete relationship explanation for every move.

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

## Live Relay

Two to four players receive the same round. Opponents see move count, hint use, and a coarse
progress band—not current nodes or routes. The first valid server-recorded finish wins; moves,
hints, and server time break near-simultaneous ties.
