# Data pipeline

The Build Week graph begins with forty reviewed anchor QIDs per category and expands through the
versioned relationship registry.

```text
anchors → cached Wikidata batches → normalized entities/edges
        → Commons metadata and license filters
        → quality and hub pruning → immutable SQLite graph
        → candidate rounds → editorial review → published bundle
```

`wbgetentities` responses are cached immutably and hashed. Normalization rejects deprecated,
unknown-value, and no-value statements. Only configured inverses are materialized. Output order is
deterministic and never relies on response order.

Graph schema v2 stores each edge's direction explicitly. Runtime relation groups use the registry's
forward label for forward edges and inverse label for inverse edges, while the edge's complete
fact-grounded explanation remains unchanged in both directions.
The reader rejects bundles whose declared schema is not v2 before reporting graph health. Real-data
normalization also provides a full deterministic relationship sentence until an approved,
fact-grounded editorial explanation replaces it.

Raw snapshots and full graph bundles are release artifacts, not Git content. The repository
contains the inputs, manifests, review records, and a tiny pipeline-generated smoke bundle.
That fixture is deliberately not a miniature knowledge claim: it contains four clearly marked
fictional story worlds with twelve uniquely named entities each. Their readable relationships use
all twenty playable property types while preserving the deterministic 48-entity, 96-edge ring
topology required by scoring tests. Its 100 candidate rounds and 40 fixture-only approvals must
never be presented as reviewed production content.

Normal development and Compose gameplay do not use that fixture. Both require
`data/builds/current` to point at a verified `bundle_kind: wikidata` pack. Missing data is an error;
there is no silent API or browser demo fallback.

The committed catalog contains 160 unique anchors, 40 per category. Its provenance manifest records
the catalog hash and the date all 160 QIDs resolved through `wbgetentities`.

```sh
uv run --package webwoven-pipeline webwoven-pipeline validate-inputs \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v1.json
uv run --package webwoven-pipeline webwoven-pipeline build-smoke
uv run --package webwoven-pipeline webwoven-pipeline verify-manifest \
  data/fixtures/smoke/manifest.json
```

## Build the local real-data playtest pack

The July 13 snapshot is reproducible from the reviewed anchors without SPARQL. Set a descriptive
Wikimedia User-Agent in `.env`, export it into the shell, then run:

```sh
set -a
. ./.env
set +a

uv run --package webwoven-pipeline webwoven-pipeline acquire \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v1.json \
  --cache data/raw/wikidata-2026-07-13 \
  --output data/builds/wikidata-2026-07-13/graph-source.json \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT" \
  --hops 2 \
  --max-entities 2500

uv run --package webwoven-pipeline webwoven-pipeline build-wikidata-pack \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v1.json \
  --graph-source data/builds/wikidata-2026-07-13/graph-source.json \
  --output data/builds/wikidata-2026-07-13/bundle \
  --created-at 2026-07-13T20:20:38Z

ln -s wikidata-2026-07-13/bundle data/builds/current
uv run --package webwoven-pipeline webwoven-pipeline verify-manifest \
  data/builds/current/manifest.json
```

The generated bundle enables 40 deterministic routes for local playtesting, but its
`round-review-status.json` truthfully records that human editorial approval is still pending.
Round starts and targets are restricted to the 160 reviewed, recognizable anchors; intermediary
nodes may come from either expansion hop. The current two-hop snapshot contains 2,214 labelled
entities and 12,130 directed playable edges. It contains real Wikidata knowledge under CC0 but no
Commons documentary media yet, so project-authored category illustrations remain the explicitly
non-documentary fallback.
