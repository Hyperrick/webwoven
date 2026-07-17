# ADR 0006: Source-neutral relationship semantics

## Status

Accepted on 2026-07-17.

## Context

Webwoven can compile Wikidata snapshots, normalized JSON imports, and synthetic fixtures. A property
identifier alone does not determine safe English copy: `P166` can point to an award, a ranked list,
or another recognition, while `P17` can connect a country to a place, language, organization, or
unclassified subject. Provider descriptions also contain incidental words such as “park,” “state,”
or “school,” so using free text as proof of a physical or organizational type creates false claims.

Relationship explanations appear in navigation cards, history, hints, and result recaps. Direction
or wording defects therefore cross acquisition, compilation, API presentation, and browser demos.

## Decision

The pipeline relationship-semantics module owns the source-neutral vocabulary. Source adapters map
provider evidence into a small set of semantic tags. Physical-place, language, and organization
verbs require explicit tags or trusted structured classifications; missing evidence falls back to
the neutral “associated with” form. Recognition context may establish a neutral recognition tag,
but award verbs still require award evidence and ranked selections use ranking or inclusion copy.

The graph compiler is the common trust boundary for every compiled source. Each explanation must be
a normalized complete sentence, mention both statement endpoints at least once, and contain
no Unicode formatting controls. `P17` and `P166` copy must match the deterministic formatter for the
supplied evidence rather than merely avoiding a list of known bad verbs. Forward and inverse
navigation copies of one statement must retain identical prose, qualifiers, and playability while
swapping endpoints and direction.

The API memory graph and browser demo graph are explicit development adapters rather than compiled
release sources. Their facts and directions are validated by dedicated tests against the same
outcomes: complete endpoint-grounded prose and direction-aligned labels.

## Consequences

- New data adapters can participate by emitting normalized entities, recognized semantic tags, and
  grounded explanations; they do not need to reproduce Wikidata's raw schema.
- Underclassification produces neutral, truthful copy instead of a confident physical, language,
  organization, award, or ranking claim.
- Semantic changes rebuild immutable graph artifacts from hash-verified source batches without
  refetching media.
- Runtime gameplay remains independent of Wikidata, Commons, and language-generation services.
