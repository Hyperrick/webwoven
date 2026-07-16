"""Verified, immutable graph-media catalog."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from webwoven_api.graph.bundle import GraphBundleError

_MEDIA_NAME = re.compile(r"^(?P<digest>[0-9a-f]{64})\.(?P<extension>gif|jpg|png|webp)$")
_MEDIA_TYPES = {
    "gif": "image/gif",
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


@dataclass(frozen=True, slots=True)
class GraphMediaAsset:
    name: str
    path: Path
    content_type: str
    sha256: str


@dataclass(frozen=True, slots=True)
class GraphMediaCatalog:
    assets: tuple[GraphMediaAsset, ...] = ()

    def get(self, name: str) -> GraphMediaAsset | None:
        return next((asset for asset in self.assets if asset.name == name), None)


def load_graph_media_catalog(manifest_path: Path) -> GraphMediaCatalog:
    """Load and hash-check every media artifact declared by an immutable bundle."""
    value: object = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GraphBundleError("unsupported graph manifest")
    payload = cast(dict[str, Any], value)
    artifacts_value = payload.get("artifacts")
    if not isinstance(artifacts_value, list):
        raise GraphBundleError("graph manifest has no artifacts")

    assets: list[GraphMediaAsset] = []
    seen: set[str] = set()
    for item in cast(list[object], artifacts_value):
        if not isinstance(item, dict):
            continue
        artifact = cast(dict[str, Any], item)
        if artifact.get("role") != "commons_media":
            continue
        relative = artifact.get("path")
        if not isinstance(relative, str):
            raise GraphBundleError("media artifact path must be a string")
        relative_path = Path(relative)
        if relative_path.parts != ("media", relative_path.name):
            raise GraphBundleError("media artifact path must be directly below media/")
        match = _MEDIA_NAME.fullmatch(relative_path.name)
        if match is None or relative_path.name in seen:
            raise GraphBundleError("media artifact name must be a unique content hash")
        expected_hash = artifact.get("sha256")
        expected_size = artifact.get("bytes")
        if (
            not isinstance(expected_hash, str)
            or expected_hash != match.group("digest")
            or not isinstance(expected_size, int)
        ):
            raise GraphBundleError("media artifact identity is invalid")
        path = manifest_path.parent / relative_path
        if not path.is_file() or path.stat().st_size != expected_size:
            raise GraphBundleError(f"media artifact is missing or truncated: {relative}")
        if _sha256(path) != expected_hash:
            raise GraphBundleError(f"media artifact checksum mismatch: {relative}")
        extension = match.group("extension")
        if not _matches_signature(path, extension):
            raise GraphBundleError(f"media artifact signature mismatch: {relative}")
        seen.add(relative_path.name)
        assets.append(
            GraphMediaAsset(
                name=relative_path.name,
                path=path,
                content_type=_MEDIA_TYPES[extension],
                sha256=expected_hash,
            )
        )
    return GraphMediaCatalog(tuple(sorted(assets, key=lambda asset: asset.name)))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _matches_signature(path: Path, extension: str) -> bool:
    with path.open("rb") as handle:
        prefix = handle.read(12)
    if extension == "jpg":
        return prefix.startswith(b"\xff\xd8\xff")
    if extension == "png":
        return prefix.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == "gif":
        return prefix.startswith((b"GIF87a", b"GIF89a"))
    return len(prefix) >= 12 and prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP"
