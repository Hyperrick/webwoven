# Data pipeline

The Build Week graph begins with forty curated anchor QIDs per category and expands through the
versioned relationship registry.

```text
anchors → cached Wikidata batches → normalized entities/edges
        → ranked exact-media discovery → Commons license filters
        → bounded local downloads and attribution records
        → quality and hub pruning → immutable SQLite graph
        → candidate rounds → deterministic validation → published bundle
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
contains the inputs, manifests, validation records, and a tiny pipeline-generated smoke bundle.
That fixture is deliberately not a miniature knowledge claim: it contains four clearly marked
fictional story worlds with twelve uniquely named entities each. Their readable relationships use
all twenty playable property types while preserving the deterministic 48-entity, 96-edge ring
topology required by scoring tests. Its 100 candidate rounds and 40 deterministic fixture
selections must never be presented as production knowledge content.

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

The release snapshot is reproducible from the curated anchors without SPARQL. Set a quoted,
descriptive Wikimedia User-Agent in `.env`, then run:

```sh
WEBWOVEN_WIKIMEDIA_USER_AGENT=$(sed -n \
  's/^WEBWOVEN_WIKIMEDIA_USER_AGENT=//p' .env)
WEBWOVEN_WIKIMEDIA_USER_AGENT=${WEBWOVEN_WIKIMEDIA_USER_AGENT#\"}
WEBWOVEN_WIKIMEDIA_USER_AGENT=${WEBWOVEN_WIKIMEDIA_USER_AGENT%\"}
SNAPSHOT_CREATED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)

uv run --package webwoven-pipeline webwoven-pipeline acquire \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v1.json \
  --cache data/raw/wikidata-2026-07-15-scale-v1 \
  --output data/builds/wikidata-2026-07-15-full-media/source.json \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT" \
  --hops 3 \
  --max-entities 5500

uv run --package webwoven-pipeline webwoven-pipeline discover-media \
  --graph-source data/builds/wikidata-2026-07-15-full-media/source.json \
  --cache data/raw/media-discovery-2026-07-15-v1 \
  --output data/builds/wikidata-2026-07-15-full-media/discovered.json \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT"

uv run --package webwoven-pipeline webwoven-pipeline acquire-commons \
  --graph-source data/builds/wikidata-2026-07-15-full-media/discovered.json \
  --output data/builds/wikidata-2026-07-15-full-media/commons \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT" \
  --created-at "$SNAPSHOT_CREATED_AT" \
  --download-interval 0.25 \
  --download-workers 16 \
  --require-complete

uv run --package webwoven-pipeline webwoven-pipeline build-wikidata-pack \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v1.json \
  --graph-source data/builds/wikidata-2026-07-15-full-media/discovered.json \
  --commons-manifest data/builds/wikidata-2026-07-15-full-media/commons/media-manifest.json \
  --output data/builds/wikidata-2026-07-15-full-media/bundle \
  --created-at "$SNAPSHOT_CREATED_AT"

ln -sfn wikidata-2026-07-15-full-media/bundle data/builds/current
uv run --package webwoven-pipeline webwoven-pipeline verify-manifest \
  data/builds/current/manifest.json
```

Download starts are globally spaced even when multiple workers overlap response bodies. When the
Commons metadata API cannot provide a resized upload URL for a small source file, acquisition uses
Wikimedia Commons' own `w/thumb.php` endpoint for a 640-pixel display derivative—or a 480-pixel
derivative for animated GIFs that would exceed the local size gate—instead of requesting the
rate-limited original upload.

Wikidata requests default to a five-second maximum replica lag, nine bounded retries, and a
quarter-second interval between uncached batches. If the service reports sustained `maxlag`, wait
for replication to recover. A non-time-sensitive snapshot may explicitly use `--max-lag` up to
120 seconds while retaining the request interval; the resulting data remains immutable and all
source responses are hashed.

The generated bundle automatically publishes 40 deterministic routes after a fail-closed quality
gate verifies their curated endpoints, labels, allowed relationships, shortest distances, and
locked category and difficulty distribution. `round-validation-report.json` records every check.
Round starts and targets are restricted to the 160 curated, recognizable anchors; intermediary
nodes may come from any expansion hop. When the final hop reaches the entity cap, its unseen
frontier is selected evenly across the four release categories instead of favoring low-numbered
QIDs. Media discovery covers every graph entity. It prefers direct depictions and exact article
lead images, then tries exact Commons categories, structured depicts matches, entity-specific
article images, and a labelled graph-neighbor context fallback. Article-page flags, stub graphics,
logos, and other generic chrome are rejected unless the filename contains entity-specific
evidence. Acquisition stores only content-addressed local raster files and records rejected
metadata or licenses. The strict build fails unless all entity mappings survive download and
manifest validation.

The full-node July 15 snapshot contains 5,482 labelled entities and 33,000 directed playable edges,
up from 2,214 and 12,130 in the two-hop playtest pack. Its 112 immutable source batches retain the
same relation registry, curated endpoints, and four-category round contract. All 5,482 nodes have
an image mapping backed by 5,062 distinct Commons source files stored locally; shared media remains
only where it has a documented exact or graph-context relationship.
The final asset pack is an exact-coverage merge: a paced repair pass recovered the transient gaps
from the bulk download, leaving 5,482 published mappings and zero rejected records. One small
source file uses its bounded original because Commons could not render a thumbnail for it.
