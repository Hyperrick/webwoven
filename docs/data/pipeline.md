# Data pipeline

The atlas begins with twenty curated anchor QIDs in each of ten categories and expands through the
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

Graph schema v3 stores each edge's direction explicitly and preserves one optional preferred
Wikipedia article URL per entity. Runtime relation groups use the registry's
forward label for forward edges and inverse label for inverse edges, while the edge's complete
fact-grounded explanation remains unchanged in both directions.
The reader rejects bundles whose declared schema is not v3 before reporting graph health. Real-data
normalization also provides a full deterministic relationship sentence until an approved,
fact-grounded editorial explanation replaces it.

Raw snapshots and full graph bundles are release artifacts, not Git content. The repository
contains the inputs, manifests, validation records, and a tiny pipeline-generated smoke bundle.
That fixture is deliberately not a miniature knowledge claim: it contains ten clearly marked
fictional story worlds with twelve uniquely named entities each. Their readable relationships use
all twenty playable property types while preserving the deterministic 120-entity, 240-edge ring
topology required by scoring tests. Its 100 candidate rounds and 40 deterministic fixture
selections must never be presented as production knowledge content.

Normal development and Compose gameplay do not use that fixture. Both require
`data/builds/current` to point at a verified `bundle_kind: wikidata` pack. Missing data is an error;
there is no silent API or browser demo fallback.

The committed v2 catalog contains 200 unique anchors, 20 per category. Its provenance manifest
records the catalog hash and the date all 200 QIDs resolved through `wbgetentities`.

```sh
uv run --package webwoven-pipeline webwoven-pipeline validate-inputs \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v2.json
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
  --seeds data/seeds/anchors.v2.json \
  --cache data/raw/wikidata-2026-07-16-taxonomy-v2 \
  --output data/builds/wikidata-2026-07-16-taxonomy-v2/graph-source.json \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT" \
  --hops 2 \
  --max-entities 10000

uv run --package webwoven-pipeline webwoven-pipeline discover-media \
  --graph-source data/builds/wikidata-2026-07-16-taxonomy-v2/graph-source.json \
  --cache data/raw/media-discovery-2026-07-16-taxonomy-v2 \
  --output data/builds/wikidata-2026-07-16-taxonomy-v2/graph-source-media-v2.json \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT"

uv run --package webwoven-pipeline webwoven-pipeline acquire-commons \
  --graph-source data/builds/wikidata-2026-07-16-taxonomy-v2/graph-source-media-v2.json \
  --output data/builds/wikidata-2026-07-16-media-assets-v1 \
  --reuse-manifest data/builds/wikidata-2026-07-15-media-assets-v13/media-manifest.json \
  --user-agent "$WEBWOVEN_WIKIMEDIA_USER_AGENT" \
  --created-at "$SNAPSHOT_CREATED_AT" \
  --download-interval 0.25 \
  --download-workers 16 \
  --require-complete

uv run --package webwoven-pipeline webwoven-pipeline build-wikidata-pack \
  --registry data/relation-registry/relations.v1.json \
  --seeds data/seeds/anchors.v2.json \
  --graph-source data/builds/wikidata-2026-07-16-taxonomy-v2/graph-source-media-v2.json \
  --commons-manifest data/builds/wikidata-2026-07-16-media-assets-v1/media-manifest.json \
  --output data/builds/wikidata-2026-07-16-ten-categories-v2 \
  --created-at "$SNAPSHOT_CREATED_AT"

ln -sfn wikidata-2026-07-16-ten-categories-v2 data/builds/current
uv run --package webwoven-pipeline webwoven-pipeline verify-manifest \
  data/builds/current/manifest.json
```

Previously verified media packs can be supplied through `--reuse-manifest`. Matching source files
are hash-verified and hard-linked into the new immutable pack where the filesystem permits it;
only new or changed Commons selections are downloaded. Download starts are globally spaced even
when multiple workers overlap response bodies. When the
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
Round starts and targets are restricted to the 200 curated, recognizable anchors; intermediary
nodes may come from any expansion hop. When the final hop reaches the entity cap, its unseen
frontier is selected evenly across the ten release categories instead of favoring low-numbered
QIDs. Media discovery covers every graph entity. It prefers direct depictions and exact article
lead images, then tries exact Commons categories, structured depicts matches, entity-specific
article images, and a labelled graph-neighbor context fallback. Article-page flags, stub graphics,
logos, and other generic chrome are rejected unless the filename contains entity-specific
evidence. Acquisition stores only content-addressed local raster files and records rejected
metadata or licenses. The strict build fails unless all entity mappings survive download and
manifest validation.

The active July 16 ten-category snapshot contains 3,970 labelled entities and 22,402 directed
playable edges. It adds 946 entities that were absent from the preceding graph. All 3,970 nodes
have a local image mapping backed by 3,621 distinct Commons files: 2,769 verified files were
reused and 852 new selections were downloaded. The strict media pass finished with zero rejected
records. Acquisition also retains Wikipedia sitelinks for 3,778 entities; bundle compilation
prefers English and falls through the supported language order without inventing article URLs.

The previous full-node July 15 snapshot contains 5,482 labelled entities and 33,000 directed playable edges,
up from 2,214 and 12,130 in the two-hop playtest pack. Its 112 immutable source batches retain the
same relation registry, curated endpoints, and four-category round contract. All 5,482 nodes have
an image mapping backed by 5,062 distinct Commons source files stored locally; shared media remains
only where it has a documented exact or graph-context relationship.
The final asset pack is an exact-coverage merge: a paced repair pass recovered the transient gaps
from the bulk download, leaving 5,482 published mappings and zero rejected records. One small
source file uses its bounded original because Commons could not render a thumbnail for it.
