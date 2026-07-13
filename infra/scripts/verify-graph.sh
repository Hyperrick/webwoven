#!/usr/bin/env sh
set -eu

bundle_dir=${1:-data/fixtures/smoke}
manifest="$bundle_dir/manifest.json"
graph="$bundle_dir/graph.sqlite3"

test -f "$manifest"
test -f "$graph"
python3 - "$manifest" "$graph" <<'PY'
import hashlib
import json
import pathlib
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
actual = hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest()
graph_entries = [
    entry for entry in manifest.get("artifacts", []) if entry.get("role") == "compiled_graph"
]
if len(graph_entries) != 1:
    raise SystemExit("manifest must contain exactly one compiled_graph artifact")
expected = graph_entries[0].get("sha256")
if expected != actual:
    raise SystemExit(f"graph checksum mismatch: expected {expected}, got {actual}")
print(f"verified graph {manifest.get('graph_build_id', 'unknown')} ({actual[:12]})")
PY
