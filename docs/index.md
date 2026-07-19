# Webwoven

Webwoven is an explainable knowledge-graph game built for OpenAI Build Week.

> Connect anything. Discover why it is connected.

Players travel from a known start to a known target by following real, named relationships.
Every move answers not only _where can I go?_ but _why are these things connected?_

![Webwoven frontispiece with three play modes](assets/screenshots/frontispiece.webp)

## Three ways to play

- **Single player** for a difficulty-selected route at your own pace
- **Daily challenge** for one shared route and leaderboard
- **Multiplayer** for a synchronized live race with two to four players

Each mode uses the same immutable, explainable atlas. A player can inspect the documented fact,
licensed image, and preferred Wikipedia article behind a node without spending a move.
Automatic assignments begin with at least two distinct destinations, and every direction presents
the same fact-aware relationship sentence.

## Two promises

The product promise is a fair and visually distinctive knowledge game. The build promise is that
**everyone with an idea can become a game developer** when an AI collaborator is paired with a
clear brief, testable decisions, and visible human judgment.

The documentation is maintained with the implementation. It records architecture, data
provenance, AI boundaries, tests, operations, and concise Build Week milestones.

## Current release

Webwoven's complete Build Week release is live at
[www.webwoven.org](https://www.webwoven.org). Single player, Daily challenge, and synchronized
Multiplayer Lobbies all run against an immutable, release-scale Wikidata bundle with locally served,
policy-checked Commons media for every graph entity. Multiplayer includes deep-link invitations
with explicit confirmation, reconnect, an authoritative 30-second grace countdown, and same-Lobby
rematch voting.

The active atlas contains 3,970 entities, 22,402 named relationships, 100 validated, published round
definitions, and ten categories. A round definition fixes its curated start/goal pair, category,
difficulty, and scoring distance—not the path the player must take. Every category offers four Easy,
four Normal, and two Hard assignments. Route-aware frontier projection retains a target-reaching
choice when one exists and turns an exhausted frontier into Back instead of presenting false
choices. The responsive map keeps complete labels, the active target, and recovery actions usable
on desktop and phone. The synthetic smoke graph remains test-only.

The current repository gate passes 164 web tests, 363 Python tests, 48 desktop/mobile Playwright flows,
both Remotion composition checks, and the repository's strict code, data, documentation, and
container checks. The public demo and Devpost draft are prepared; rights confirmation, final owner
review, and submission remain outside the repository.

Start with the [game rules](product/game-rules.md), [system map](architecture/system-map.md),
[architecture](architecture/overview.md),
[data pipeline](data/pipeline.md), or the [current build log](build-log/2026-07-19.md).
