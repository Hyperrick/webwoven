from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from webwoven_api.graph.bundle import GraphBundleError
from webwoven_api.graph.media import (
    GraphMediaAsset,
    GraphMediaCatalog,
    load_graph_media_catalog,
)


def test_media_route_serves_only_catalogued_content_addressed_assets(
    client: TestClient,
    tmp_path: Path,
) -> None:
    body = b"\xff\xd8\xffverified-media"
    digest = hashlib.sha256(body).hexdigest()
    path = tmp_path / f"{digest}.jpg"
    path.write_bytes(body)
    asset = GraphMediaAsset(path.name, path, "image/jpeg", digest)
    client.app.state.container = replace(
        client.app.state.container,
        media=GraphMediaCatalog((asset,)),
    )

    response = client.get(f"/api/v1/media/{path.name}")

    assert response.status_code == 200
    assert response.content == body
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert response.headers["etag"] == f'"{digest}"'
    assert client.get("/api/v1/media/not-catalogued.jpg").status_code == 404


def test_media_catalog_rejects_tampered_manifest_artifact(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    body = b"\x89PNG\r\n\x1a\nverified-media"
    digest = hashlib.sha256(body).hexdigest()
    asset = media / f"{digest}.png"
    asset.write_bytes(body)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "path": f"media/{asset.name}",
                        "role": "commons_media",
                        "bytes": len(body),
                        "sha256": digest,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert load_graph_media_catalog(manifest).get(asset.name) is not None

    asset.write_bytes(body + b"changed")
    with pytest.raises(GraphBundleError, match="truncated"):
        load_graph_media_catalog(manifest)
