#!/usr/bin/env sh
set -eu

bundle_dir=${1:-data/builds/current}
manifest="$bundle_dir/manifest.json"
graph="$bundle_dir/graph.sqlite3"

test -f "$manifest"
test -f "$graph"
python3 - "$manifest" "$graph" <<'PY'
import hashlib
import json
import pathlib
import sqlite3
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
graph_path = pathlib.Path(sys.argv[2])
if manifest.get("bundle_kind") != "wikidata":
    raise SystemExit("deployment requires a Wikidata graph bundle")
if manifest.get("graph_schema_version") != 2:
    raise SystemExit("deployment requires graph schema v2")
if not manifest.get("source_batches"):
    raise SystemExit("Wikidata bundle has no source batch provenance")
actual = hashlib.sha256(graph_path.read_bytes()).hexdigest()
graph_entries = [
    entry for entry in manifest.get("artifacts", []) if entry.get("role") == "compiled_graph"
]
if len(graph_entries) != 1:
    raise SystemExit("manifest must contain exactly one compiled_graph artifact")
expected = graph_entries[0].get("sha256")
if expected != actual:
    raise SystemExit(f"graph checksum mismatch: expected {expected}, got {actual}")
with sqlite3.connect(f"file:{graph_path}?mode=ro", uri=True) as connection:
    metadata = dict(connection.execute("SELECT key, value FROM metadata"))
if metadata.get("graph_build_id") != manifest.get("graph_build_id"):
    raise SystemExit("graph build ID does not match manifest")
if metadata.get("schema_version") != "2":
    raise SystemExit("compiled graph is not schema v2")
print(f"verified graph {manifest.get('graph_build_id', 'unknown')} ({actual[:12]})")
PY
