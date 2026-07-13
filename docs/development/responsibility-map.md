# Responsibility map

Code is grouped around owners rather than technical convenience. Each rule or piece of mutable
state has one owner and is consumed through a narrow contract.

| Concern                       | Owner                      | Adapters and consumers                             |
| ----------------------------- | -------------------------- | -------------------------------------------------- |
| Legal moves and visible trail | Navigation domain          | Session service, web controller                    |
| Frozen decision frontiers     | Session exploration domain | Persistence, API presenter, map board              |
| Score and time windows        | Scoring domain             | Session completion, results UI                     |
| Hint choice and penalties     | Hints domain               | Session commands, hint presentation                |
| Entity and edge lookup        | `GraphReader`              | SQLite adapter, session service, pipeline compiler |
| Guest identity                | Guest service              | Cookie/HTTP adapter, PostgreSQL repository         |
| Daily assignment and ranking  | Daily service              | Repository, REST routes                            |
| Race lifecycle and reconnect  | Room service               | Valkey adapter, WebSocket routes                   |
| Open-data acquisition         | Pipeline acquisition       | HTTP transport, immutable cache                    |
| Round curation                | Pipeline round builder     | Review records, graph compiler                     |
| Deterministic widening map    | `MapBoard` domain          | Svelte and Three.js presentation adapters          |
| Rendering and interaction     | Svelte feature components  | API facade and domain view models                  |

Cross-domain code is shared only when it represents a stable concept with multiple real consumers.
There are no global grab-bag utilities, god services, or UI components that combine transport,
game-rule enforcement, and rendering.
