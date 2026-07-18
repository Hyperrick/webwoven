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

The API retains the `rooms` resource name while the user-facing product calls each room a Lobby.
Rooms use six-character Crockford Base32 codes and accept two to four active guests.

| Method | Path                            | Purpose |
| ------ | ------------------------------- | ------- |
| `POST` | `/api/v1/rooms`                 | Create a Lobby and pin its route filters. |
| `GET`  | `/api/v1/rooms/{code}/invite`   | Read the minimal invitation preview before confirmation. |
| `POST` | `/api/v1/rooms/{code}/join`     | Join a still-open Lobby. |
| `POST` | `/api/v1/rooms/{code}/ready`    | Change the current participant's ready state. |
| `POST` | `/api/v1/rooms/{code}/start`    | Let the host create synchronized sessions and start the countdown. |
| `POST` | `/api/v1/rooms/{code}/rematch`  | Submit the current participant's yes/no rematch vote. |
| `GET`  | `/api/v1/rooms/{code}`          | Return the current member's reconnectable Lobby snapshot. |

`POST /api/v1/rooms` requires `difficulty` and accepts an optional canonical `category`; when
present, both round endpoints match that category. Omitting it selects from every eligible
category. The selected round is pinned when the host creates the Lobby, so joiners cannot change
the filter. Moves still use the shared session command endpoint.

```json
{
  "difficulty": "normal",
  "category": "science_technology"
}
```

The host-only Share action creates the browser route `/relay/{CODE}/join`. It invokes the native Web
Share API when available, with clipboard and selectable-text fallbacks. The route first requests
`GET /api/v1/rooms/{code}/invite`, whose response is intentionally limited to `code`,
`host_display_name`, room `state`, `player_count`, `max_players`, `is_member`, and `joinable`. The
client names the inviter and requires an explicit confirmation before it calls the join endpoint or
opens an existing membership in the current Webwoven window.

Every Lobby snapshot exposes `countdown_ends_at`, `grace_ends_at`, `rematch_ends_at`, and an optional
`close_reason`. Participant entries expose `active` and the optional `rematch_vote`; another
participant's session ID remains hidden. Session command authorization uses the same absolute
countdown boundary as the sessions themselves, so a command at the deadline does not depend on a
room refresh. The first finish opens a 30-second grace window. At its deadline unfinished sessions
are marked `expired`, the room enters `finished`, and a 30-second rematch vote begins. At least two
yes votes retain the code and create new synchronized sessions for those voters; fewer than two
closes the room with `not_enough_players`.

`/api/v1/ws/rooms/{code}` emits roster, countdown, abstract progress, participant finish,
grace-period, rematch-vote, next-countdown, and closure events. Its transition-aware wait wakes at
the next authoritative deadline rather than waiting for a later client action. A reconnect begins
with a resume message and receives a complete snapshot before incremental events continue.

## Reports and health

`POST /api/v1/content-reports` records a structured content concern without third-party tracking.
The unversioned `/health/live`, `/health/ready`, and `/health/graph` endpoints separate process,
dependency, and graph-bundle health.

The generated OpenAPI document is the executable contract. Client types are regenerated from it
and checked for drift in CI.
