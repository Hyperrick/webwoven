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
