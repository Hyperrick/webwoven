# Delivery and acceptance

Webwoven uses an internal submission freeze of 2026-07-21 at 22:00 CEST, four hours before the
currently published deadline of July 21 at 5:00 PM Pacific. Infrastructure spending and final
submission remain explicit human decisions.

The [OpenAI Build Week page](https://openai.com/build-week/),
[Devpost overview](https://openai.devpost.com/), [official rules](https://openai.devpost.com/rules),
and [FAQ](https://openai.devpost.com/details/faqs) were rechecked on 2026-07-18. The current judging
criteria are technological implementation, design, potential impact, and quality of the idea.
Rules and submission fields must still be checked immediately before submission because the
organizers may update them during the event.

## Current submission gate

The current official requirements call for:

- one working project built meaningfully with Codex and GPT-5.6 in a single best-fit track;
- an English project description that explains the features and functionality;
- a public YouTube demonstration with audio, no longer than three minutes, showing the working
  project and specifically explaining how Codex and GPT-5.6 were used;
- a public, appropriately licensed repository with setup and testing instructions plus a README
  that distinguishes Codex acceleration from the creator's key decisions;
- the `/feedback` Session ID from the primary Codex build task; and
- free judge access to the working project through the judging period.

Webwoven currently satisfies the working-product, public-repository, MIT-license, English-copy,
live-access, dated-history, and GPT-5.6 evidence gates. The prepared
[Devpost draft](../submission/devpost.md) uses the **Education** track and includes the story,
testing path, upload-ready media, and a timed demo script.

The primary `/feedback` Session ID has been recorded, the 2:31 narrated demo is public on YouTube,
and the project owner has approved the final video and confirmed individual entrant eligibility.
The remaining human-controlled gates are the final third-party-rights declaration, review of the
completed Devpost draft, any CAPTCHA or legal acceptance Devpost requires, and the final submit
action.

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
