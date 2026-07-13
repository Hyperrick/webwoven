from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

from .compiler import GRAPH_SCHEMA_VERSION


class ManifestError(ValueError):
    """Raised when a bundle manifest cannot be created or verified."""


def build_manifest(
    graph_path: Path,
    artifacts: Iterable[tuple[Path, str]],
    *,
    graph_build_id: str,
    created_at: str,
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
    artifacts_value = payload.get("artifacts")
    if not isinstance(artifacts_value, list) or not artifacts_value:
        raise ManifestError("manifest has no artifacts")
    artifacts = cast(list[Any], artifacts_value)
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
