# ADR 0004: Ten-category atlas

- Status: accepted; publication budget superseded by ADR 0008
- Date: 2026-07-16

## Context

The original four categories combined unrelated subjects such as biography and political history,
or scientific methods and natural objects. They did not give players a useful preview of a round
and produced an uneven graph dominated by two broad starter branches.

## Decision

The canonical taxonomy contains ten categories: People; History & Society; Science & Technology;
Nature & Life; Places & Architecture; Art & Design; Literature & Language; Music & Performance;
Film & Media; and Sports & Games.

Each category owns twenty reviewed, live-verified Wikidata anchors. Acquisition propagates the
anchor category through its bounded graph expansion, balances capped frontiers in canonical
category order, and restricts round endpoints to the reviewed anchor catalog. The global round
budget remains 100 candidates and 40 published routes: ten candidates and four published routes
per category.

Media is refreshed with the taxonomy. A new build may reuse an earlier hash-verified Commons file,
but it must run discovery for every entity, download every new or changed selection, retain full
license evidence, and fail unless coverage is complete.

## Consequences

- Category labels and accents are shared presentation metadata rather than duplicated UI strings.
- Smoke data expands to ten isolated stories so every category and distribution rule is exercised.
- Older four-category bundles remain immutable historical artifacts but are not compatible with
  the v2 runtime taxonomy.
- The category field describes the acquisition branch and round collection, not a claim that every
  intermediary has exactly one universally correct subject classification.
