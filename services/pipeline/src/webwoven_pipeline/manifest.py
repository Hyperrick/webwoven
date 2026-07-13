from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Literal, cast

from .compiler import GRAPH_SCHEMA_VERSION


class ManifestError(ValueError):
    """Raised when a bundle manifest cannot be created or verified."""


def build_manifest(
    graph_path: Path,
    artifacts: Iterable[tuple[Path, str]],
    *,
    graph_build_id: str,
    created_at: str,
    bundle_kind: Literal["wikidata", "test_fixture"],
    source_batches: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    artifact_values: list[dict[str, Any]] = []
    graph_parent = graph_path.parent
    for path, role in sorted(artifacts, key=lambda item: item[0].as_posix()):
        if not path.is_file():
            raise ManifestError(f"artifact does not exist: {path}")
        try:
            relative_path = path.relative_to(graph_parent).as_posix()
        except ValueError:
            relative_path = path.name
        artifact_values.append(
            {
                "path": relative_path,
                "role": role,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return {
        "manifest_version": 1,
        "graph_schema_version": GRAPH_SCHEMA_VERSION,
        "graph_build_id": graph_build_id,
        "bundle_kind": bundle_kind,
        "created_at": created_at,
        "artifacts": artifact_values,
        "source_batches": sorted(
            (dict(item) for item in source_batches),
            key=lambda item: str(item.get("path", "")),
        ),
    }


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to replace manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")


def verify_manifest(path: Path) -> None:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ManifestError("unsupported manifest")
    payload = cast(dict[str, Any], value)
    if payload.get("manifest_version") != 1:
        raise ManifestError("unsupported manifest")
    if payload.get("graph_schema_version") != GRAPH_SCHEMA_VERSION:
        raise ManifestError("unsupported graph schema version")
    bundle_kind = payload.get("bundle_kind")
    if bundle_kind not in {"wikidata", "test_fixture"}:
        raise ManifestError("unsupported bundle kind")
    source_batches = payload.get("source_batches")
    if not isinstance(source_batches, list):
        raise ManifestError("source_batches must be a list")
    if bundle_kind == "wikidata" and not source_batches:
        raise ManifestError("Wikidata bundles require source batches")
    if bundle_kind == "test_fixture" and source_batches:
        raise ManifestError("test fixtures cannot declare external source batches")
    artifacts_value = payload.get("artifacts")
    if not isinstance(artifacts_value, list) or not artifacts_value:
        raise ManifestError("manifest has no artifacts")
    artifacts = cast(list[Any], artifacts_value)
    compiled_graphs: list[Path] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ManifestError("artifact record must be an object")
        artifact_object = cast(dict[str, Any], artifact)
        relative = artifact_object.get("path")
        expected_size = artifact_object.get("bytes")
        expected_hash = artifact_object.get("sha256")
        unsafe_path = (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        )
        if unsafe_path:
            raise ManifestError("artifact path must be safe and relative")
        assert isinstance(relative, str)
        artifact_path = path.parent / relative
        if not artifact_path.is_file():
            raise ManifestError(f"artifact is missing: {relative}")
        if artifact_path.stat().st_size != expected_size or _sha256(artifact_path) != expected_hash:
            raise ManifestError(f"artifact does not match manifest: {relative}")
        if artifact_object.get("role") == "compiled_graph":
            compiled_graphs.append(artifact_path)
    if len(compiled_graphs) != 1:
        raise ManifestError("manifest must contain exactly one compiled graph")
    _verify_graph_identity(compiled_graphs[0], payload)


def _verify_graph_identity(graph_path: Path, manifest: Mapping[str, Any]) -> None:
    try:
        with sqlite3.connect(f"file:{graph_path.as_posix()}?mode=ro", uri=True) as connection:
            rows = connection.execute(
                "SELECT key, value FROM metadata WHERE key IN ('graph_build_id', 'schema_version')"
            ).fetchall()
    except sqlite3.Error as exc:
        raise ManifestError("compiled graph metadata is unreadable") from exc
    metadata = {str(key): str(value) for key, value in rows}
    if metadata.get("graph_build_id") != manifest.get("graph_build_id"):
        raise ManifestError("compiled graph build ID does not match manifest")
    if metadata.get("schema_version") != str(manifest.get("graph_schema_version")):
        raise ManifestError("compiled graph schema does not match manifest")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
