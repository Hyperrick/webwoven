# Responsibility map

Code is grouped around owners rather than technical convenience. Each rule or piece of mutable
state has one owner and is consumed through a narrow contract.

| Concern                                        | Owner                           | Adapters and consumers                             |
| ---------------------------------------------- | ------------------------------- | -------------------------------------------------- |
| Legal moves, active route, and visible trail   | Navigation domain               | Session service, web controller                    |
| Frozen decision frontiers                      | Session exploration domain      | Persistence, API presenter, map board              |
| Score and time windows                         | Scoring domain                  | Session completion, results UI                     |
| Hint choice and penalties                      | Hints domain                    | Session commands, hint presentation                |
| Entity and edge lookup                         | `GraphReader`                   | SQLite adapter, session service, pipeline compiler |
| Choice-first round eligibility                 | Pipeline round builder          | Compiler, API invariant verifier, game modes       |
| Guest identity                                 | Guest service                   | Cookie/HTTP adapter, PostgreSQL repository         |
| Daily assignment and ranking                   | Daily service                   | Repository, REST routes                            |
| Race lifecycle and reconnect                   | Room service                    | Valkey adapter, WebSocket routes                   |
| Open-data acquisition                          | Pipeline acquisition            | HTTP transport, immutable cache                    |
| Relationship semantics and explanation quality | Pipeline relationship semantics | Wikidata normalization, compiler, semantic refresh |
| Round curation                                 | Pipeline round builder          | Review records, graph compiler                     |
| Deterministic widening map                     | `MapBoard` domain               | Svelte and Three.js presentation adapters          |
| Spatial canvas camera                          | Map-camera presentation         | Gestures, controls, Three.js and SVG view adapters |
| Historical path inspection                     | Map inspection projection       | Read-only Svelte inspector                         |
| Rendering and interaction                      | Svelte feature components       | API facade and domain view models                  |

Cross-domain code is shared only when it represents a stable concept with multiple real consumers.
There are no global grab-bag utilities, god services, or UI components that combine transport,
game-rule enforcement, and rendering.
