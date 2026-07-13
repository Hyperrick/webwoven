"""Fail-closed graph-bundle identity and integrity loading."""

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

from webwoven_api.graph.sqlite_reader import GRAPH_SCHEMA_VERSION, SQLiteGraphReader

BundleKind = Literal["wikidata", "test_fixture"]


class GraphBundleError(ValueError):
    """Raised when a configured graph is incomplete, mismatched, or disallowed."""


def load_graph_bundle(
    graph_path: Path,
    manifest_path: Path,
    *,
    required_kind: BundleKind,
) -> SQLiteGraphReader:
    manifest = _manifest(manifest_path)
    if manifest.get("bundle_kind") != required_kind:
        raise GraphBundleError(f"runtime requires a {required_kind} graph bundle")
    if manifest.get("graph_schema_version") != int(GRAPH_SCHEMA_VERSION):
        raise GraphBundleError("graph manifest declares an unsupported schema")
    source_batches = manifest.get("source_batches")
    if not isinstance(source_batches, list):
        raise GraphBundleError("graph manifest has invalid source batches")
    if required_kind == "wikidata" and not source_batches:
        raise GraphBundleError("Wikidata graph bundle has no source batches")
    if required_kind == "test_fixture" and source_batches:
        raise GraphBundleError("test graph bundle declares external source batches")

    compiled = _compiled_artifact(manifest)
    artifact_path = (manifest_path.parent / _string(compiled, "path")).resolve()
    if artifact_path != graph_path.resolve():
        raise GraphBundleError("manifest compiled graph path does not match configuration")
    if graph_path.stat().st_size != compiled.get("bytes"):
        raise GraphBundleError("compiled graph size does not match manifest")
    if _sha256(graph_path) != compiled.get("sha256"):
        raise GraphBundleError("compiled graph hash does not match manifest")

    graph = SQLiteGraphReader(graph_path)
    if graph.graph_version != manifest.get("graph_build_id"):
        raise GraphBundleError("compiled graph build ID does not match manifest")
    return graph


def _manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Graph manifest not found: {path}")
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GraphBundleError("unsupported graph manifest")
    manifest = cast(dict[str, Any], value)
    if manifest.get("manifest_version") != 1:
        raise GraphBundleError("unsupported graph manifest")
    return manifest


def _compiled_artifact(manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise GraphBundleError("graph manifest has no artifacts")
    matches: list[dict[str, Any]] = []
    for item in cast(list[object], artifacts):
        if not isinstance(item, dict):
            continue
        record = cast(dict[str, Any], item)
        if record.get("role") == "compiled_graph":
            matches.append(record)
    if len(matches) != 1:
        raise GraphBundleError("graph manifest must identify one compiled graph")
    return matches[0]


def _string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise GraphBundleError(f"graph manifest {key} must be a string")
    path = Path(item)
    if path.is_absolute() or ".." in path.parts:
        raise GraphBundleError("graph manifest artifact path is unsafe")
    return item


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
