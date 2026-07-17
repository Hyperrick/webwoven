# Delivery and acceptance

Webwoven uses an internal submission freeze of 2026-07-21 at 22:00 CEST, four hours before the
currently published deadline of July 21 at 5:00 PM Pacific. Infrastructure spending and final
submission remain explicit human decisions.

The [OpenAI Build Week page](https://openai.com/build-week/) and
[Devpost overview](https://openai.devpost.com/) were checked on 2026-07-13. They describe Codex as
the building collaborator and list technical implementation, coherent design, impact, and idea
quality as judging criteria. Eligibility, submission fields, and the complete official rules must
be checked again immediately before submission because those pages can change during the event.

## Build Week milestones

The project reached its midpoint with the core playable scope already deployed: all three modes,
the production atlas, responsive map layouts, attribution, multiplayer reconnect, and
privacy-minimized reporting are live. The dated plan below remains the delivery baseline; completed
later-stage items were intentionally pulled forward when their dependencies were ready.

| Date    | Outcome                                                                                             |
| ------- | --------------------------------------------------------------------------------------------------- |
| July 13 | Repository, living documentation, design tokens, quality gates, and first playable foundation.      |
| July 14 | Versioned Wikidata and Commons acquisition, relation registry, provenance, and smoke graph.         |
| July 15 | Indexed graph, 100 candidates, 40 automatically validated rounds, and pure game engine.             |
| July 16 | API contracts, guest sessions, scoring, hints, and Solo.                                            |
| July 17 | Daily, leaderboard, attribution, Cartographer pipeline, and visual pass.                            |
| July 18 | Multiplayer lobby, countdown, room streams, expiry, and reconnect.                                  |
| July 19 | Generate, validate, manually review, and approve the Codex-assisted content pack and illustrations. |
| July 20 | Accessibility, security, data, browser, visual, and load verification; deployment images.           |
| July 21 | Approved deployment, demo recording, documentation freeze, and submission materials.                |

## Midpoint focus

The remaining half of the week concentrates on evidence and finish quality:

- accessibility, keyboard, reduced-motion, and assistive-technology verification;
- security, load, backup-restore, and production recovery checks;
- final review of Codex-assisted content and provenance records;
- demo capture, submission copy, and a documentation freeze.

## Release acceptance

The game needs 2,500–10,000 playable entities, ten categories, 100 round candidates, 40
automatically validated production rounds, three deterministic hints, and passing Solo, Daily, and
Live Relay browser flows. Every
published media record needs complete provenance and attribution. Gameplay must make no Wikidata,
Commons, or AI request.

The credential-free Compose stack must produce the web client, API, documentation, PostgreSQL,
Valkey, and a healthy local graph. The submission is AI-complete when approved Codex-assisted
artifacts, validation records, and the provenance manifest exist.
