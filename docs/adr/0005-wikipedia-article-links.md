# ADR 0005: Preserve preferred Wikipedia article links

- Status: accepted
- Date: 2026-07-16

## Context

Acquisition already stores bounded Wikipedia sitelinks for media discovery, but graph compilation
discarded them. The node inspector could therefore show Wikidata identity and Commons image
provenance without offering the corresponding readable encyclopedia article.

## Decision

Graph schema v3 stores one optional `wikipedia_url` on each entity. Bundle construction selects the
first available article using the existing deterministic language priority, preferring English.
The compiler and API accept only canonical HTTPS `*.wikipedia.org/wiki/...` URLs without query or
fragment components.

The inspector exposes the stored URL as “Read on Wikipedia” in a new tab. It does not synthesize a
URL from an entity label, and nodes without an acquired sitelink show no link.

## Consequences

- Article destinations remain pinned to the same immutable acquisition snapshot as the graph.
- The runtime does not copy, proxy, or redistribute Wikipedia article text.
- Older graph schemas remain immutable historical artifacts and are rejected by the v3 reader.
