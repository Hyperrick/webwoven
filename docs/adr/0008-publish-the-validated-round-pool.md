# ADR 0008: Publish the validated round pool

## Status

Accepted on 2026-07-18. Supersedes the 40-route publication budget in ADR 0004.

## Context

The ten-category pipeline generated 100 unique route candidates but published only 40. The
published quota per category was two Easy, one Normal, and one Hard route. The selector correctly
cycled through unseen routes and used a cryptographically strong random choice, yet an exact
category on Normal or Hard contained only one option. Remembering the player's setup therefore
made those routes repeat on every new game; no selection algorithm can create variety from a
singleton pool without silently ignoring the chosen filters.

All 100 candidates already passed the same fail-closed release checks: reviewed endpoints, matching
category, labels, allowed relationships, correct shortest distance and time window, distinct
endpoints, and at least two opening choices. Their entities, relationships, media, attribution, and
source batches were already present in the immutable graph bundle.

## Decision

Publish all 100 validated candidates under `deterministic-round-publication-v3`. Every category
owns four Easy, four Normal, and two Hard routes; the global pools contain 40 Easy, 40 Normal, and
20 Hard routes. The change rebuilds the smoke fixture and the immutable real-data graph, but does
not fetch or alter Wikidata or Commons content.

Selection history is read per player and graph version. The cycle algorithm still applies the
requested category and difficulty before choosing, and ignores history entries outside that
eligible set. This keeps the filters strict while carrying repeat avoidance across changes between
**Any category** and an exact category.

## Consequences

- No exact category-and-difficulty pool is a singleton; Hard alternates between two routes and Easy
  and Normal exhaust four routes before a repeat.
- The graph build ID changes and existing history starts a new cycle when the new immutable bundle
  is promoted.
- Daily and Multiplayer can select from the larger validated pool without runtime data or AI requests.
- Pipeline, API, smoke-fixture, browser, documentation, and submission counts move together.
- The generated candidates no longer carry a reserve status; future quality tiers require a new
  explicit policy rather than an implicit unpublished pool.
