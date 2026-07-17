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
bundle_dir = pathlib.Path(sys.argv[1]).parent
if manifest.get("bundle_kind") != "wikidata":
    raise SystemExit("deployment requires a Wikidata graph bundle")
if manifest.get("graph_schema_version") != 3:
    raise SystemExit("deployment requires graph schema v3")
if not manifest.get("source_batches"):
    raise SystemExit("Wikidata bundle has no source batch provenance")
artifacts = manifest.get("artifacts", [])
if not isinstance(artifacts, list) or not artifacts:
    raise SystemExit("manifest has no artifacts")
graph_entries = []
for entry in artifacts:
    relative = entry.get("path") if isinstance(entry, dict) else None
    if not isinstance(relative, str):
        raise SystemExit("manifest artifact path is invalid")
    relative_path = pathlib.Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise SystemExit(f"unsafe manifest artifact path: {relative}")
    artifact_path = bundle_dir / relative_path
    if not artifact_path.is_file():
        raise SystemExit(f"manifest artifact is missing: {relative}")
    actual_size = artifact_path.stat().st_size
    expected_size = entry.get("bytes")
    if actual_size != expected_size:
        raise SystemExit(
            f"artifact size mismatch for {relative}: expected {expected_size}, got {actual_size}"
        )
    actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    expected_hash = entry.get("sha256")
    if actual_hash != expected_hash:
        raise SystemExit(
            f"artifact checksum mismatch for {relative}: expected {expected_hash}, got {actual_hash}"
        )
    if entry.get("role") == "compiled_graph":
        graph_entries.append(entry)
if len(graph_entries) != 1:
    raise SystemExit("manifest must contain exactly one compiled_graph artifact")
actual = hashlib.sha256(graph_path.read_bytes()).hexdigest()
with sqlite3.connect(f"file:{graph_path}?mode=ro", uri=True) as connection:
    metadata = dict(connection.execute("SELECT key, value FROM metadata"))
if metadata.get("graph_build_id") != manifest.get("graph_build_id"):
    raise SystemExit("graph build ID does not match manifest")
if metadata.get("schema_version") != "3":
    raise SystemExit("compiled graph is not schema v3")
print(f"verified graph {manifest.get('graph_build_id', 'unknown')} ({actual[:12]})")
PY
