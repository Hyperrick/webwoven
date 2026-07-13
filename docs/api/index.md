# Public API

The HTTP API is versioned under `/api/v1`. Gameplay changes are commands, not arbitrary state
patches. Each command carries a client-generated idempotency key and the state version the client
last observed.

## Identity and discovery

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/guests` | Create a signed guest session. |
| `PATCH` | `/api/v1/guests/me` | Update the guest display name. |
| `GET` | `/api/v1/config` | Read public gameplay and graph versions. |
| `GET` | `/api/v1/daily` | Read the current UTC Daily assignment. |
| `GET` | `/api/v1/leaderboards/daily` | Read the pseudonymous Daily board. |

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
`incoming`.

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
