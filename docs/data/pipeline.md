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

Raw snapshots and full graph bundles are release artifacts, not Git content. The repository
contains the inputs, manifests, review records, and a tiny pipeline-generated smoke bundle.

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
