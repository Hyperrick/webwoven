# ADR 0001: Build Week architecture

## Status

Accepted on 2026-07-13.

## Decision

Use a static Svelte client, FastAPI service, PostgreSQL durable state, Valkey real-time state, and
an immutable SQLite graph compiled offline from versioned Wikidata and Commons snapshots.

All gameplay decisions are deterministic and server-authoritative. Codex-assisted content is
generated during development, schema-validated, fact-grounded, manually approved, and compiled as
static data with deterministic template fallbacks. The first release favors a portable indexed
SQLite bundle over custom CSR serialization; `GraphReader` keeps that storage decision replaceable.

## Consequences

The game remains playable during external outages and sessions are reproducible. The pipeline and
runtime require separate contracts and validation, but neither the web client nor API depends on
public knowledge endpoints.
