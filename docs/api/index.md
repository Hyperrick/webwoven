# Public API

The HTTP API is versioned under `/api/v1`. Gameplay changes are commands, not arbitrary state
patches. Each command carries a client-generated idempotency key and the state version the client
last observed.

## Identity and discovery

| Method  | Path                         | Purpose                                  |
| ------- | ---------------------------- | ---------------------------------------- |
| `POST`  | `/api/v1/guests`             | Create a signed guest session.           |
| `GET`   | `/api/v1/guests/me`          | Resume the current signed guest.         |
| `PATCH` | `/api/v1/guests/me`          | Update the guest display name.           |
| `GET`   | `/api/v1/config`             | Read public gameplay and graph versions. |
| `GET`   | `/api/v1/daily`              | Read the current UTC Daily assignment.   |
| `GET`   | `/api/v1/leaderboards/daily` | Read the pseudonymous Daily board.       |

## Sessions

`POST /api/v1/sessions` starts a round and `GET /api/v1/sessions/{id}` returns its current
snapshot. `POST /api/v1/sessions/{id}/commands` accepts one of three commands:

- `follow_edge` with a signed edge token;
- `back` to return to the prior stack node while recording another visible move;
- `use_hint` with a hint type and, for Compass, the selected relationship group.

Duplicate `client_command_id` values return the original result. A stale
`expected_state_version` returns `409` with the latest authoritative snapshot.

Session snapshots expose the round's `optimal_distance` so clients present the same par used by
server scoring. Each relation group retains its semantic Wikidata `property_id` and also receives a
stable `group_id` derived from property, direction, and label; clients use `group_id` for interface
identity and `property_id` for graph and hint semantics. Direction is explicitly `outgoing` or
`incoming`. For dense entities, the snapshot includes at most six distinct target entities. A
pure route-safe selector uses precompiled distances to retain a distance-reducing destination
whenever one remains available while varying the visible relation types; it never changes graph
truth or accepts a move that is not a stored edge. A legitimately exhausted branch remains empty so
the client can present the Back recovery action.

Snapshots also expose `navigation_stack` and `decision_history`. The navigation stack is the
current reversible route. Decision history is the immutable exploration record used by the
ever-widening map. Each zero-based stage contains its source, destination, `follow` or `back`
action, the exact visible choices, and an optional selected choice ID. Each historical destination
keeps a deterministic primary relationship and statement for compact clients plus a token-free
`connections` collection containing every grounded fact that supported the move. Only the current
`relation_groups` are actionable. Old serialized sessions without decision history load with an
empty history, while new sessions round-trip it through persistence and reconnect.

## Rooms

Rooms use six-character Crockford Base32 codes and accept two to four guests. The lifecycle API
creates or joins a room, changes readiness, starts the countdown, and returns a reconnectable
snapshot. Moves still use the shared session command endpoint.

`/api/v1/ws/rooms/{code}` emits roster, countdown, abstract progress, finish, grace-period, and
closure events. A reconnect begins with a resume message and receives a complete snapshot before
incremental events continue.

## Reports and health

`POST /api/v1/content-reports` records a structured content concern without third-party tracking.
The unversioned `/health/live`, `/health/ready`, and `/health/graph` endpoints separate process,
dependency, and graph-bundle health.

The generated OpenAPI document is the executable contract. Client types are regenerated from it
and checked for drift in CI.
