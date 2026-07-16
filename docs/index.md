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

## Two promises

The product promise is a fair and visually distinctive knowledge game. The build promise is that
**everyone with an idea can become a game developer** when an AI collaborator is paired with a
clear brief, testable decisions, and visible human judgment.

The documentation is maintained with the implementation. It records architecture, data
provenance, AI boundaries, tests, operations, and concise Build Week milestones.

## Current milestone

The repository is in the Build Week implementation phase. Normal local gameplay now runs against
an immutable, release-scale Wikidata bundle with locally served, policy-checked Commons media for
every graph entity.
The active atlas contains 3,970 entities, 22,402 named relationships, 100 validated candidates,
40 published routes, and ten categories. The synthetic smoke graph remains test-only; production
load validation is the next data milestone.

Start with the [game rules](product/game-rules.md), [architecture](architecture/overview.md),
[data pipeline](data/pipeline.md), or the [current build log](build-log/2026-07-16.md).
