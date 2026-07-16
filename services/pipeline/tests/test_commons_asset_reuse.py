from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from pathlib import Path

from webwoven_pipeline.commons_assets import acquire_commons_assets
from webwoven_pipeline.http_transport import BinaryResponse
from webwoven_pipeline.models import MediaRecord


class MetadataClient:
    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        return {
            file_name: replace(
                _record(),
                file_name=file_name,
                derivative_url=f"https://upload.wikimedia.org/{file_name}",
            )
            for file_name in file_names
        }


class BinaryTransport:
    def get_bytes(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
    ) -> BinaryResponse:
        return BinaryResponse(
            body=b"\xff\xd8\xff" + url.rpartition("/")[2].encode(),
            content_type="image/jpeg",
            final_url=url,
        )


def test_acquisition_reuses_verified_assets_and_downloads_only_new_files(
    tmp_path: Path,
) -> None:
    previous = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "previous",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=MetadataClient(),
        binary_transport=BinaryTransport(),
        download_interval=0,
    )

    refreshed = acquire_commons_assets(
        {"Q1": "Portrait.jpg", "Q2": "New.jpg"},
        ("Q1", "Q2"),
        tmp_path / "refreshed",
        user_agent="webwoven tests",
        created_at="2026-07-16T12:00:00Z",
        metadata_client=MetadataClient(),
        binary_transport=BinaryTransport(),
        download_interval=0,
        reuse_bundle=previous,
        require_complete=True,
    )

    manifest = json.loads(refreshed.manifest_path.read_text(encoding="utf-8"))
    assert refreshed.file_by_entity == {"Q1": "Portrait.jpg", "Q2": "New.jpg"}
    assert manifest["coverage"]["reused_assets"] == 1
    assert manifest["coverage"]["downloaded_assets"] == 1
    previous_path = (
        previous.manifest_path.parent / previous.assets_by_file["Portrait.jpg"].asset_path
    )
    refreshed_path = (
        refreshed.manifest_path.parent / refreshed.assets_by_file["Portrait.jpg"].asset_path
    )
    assert previous_path.stat().st_ino == refreshed_path.stat().st_ino


def _record() -> MediaRecord:
    return MediaRecord(
        file_name="Portrait.jpg",
        original_url="https://upload.wikimedia.org/portrait.jpg",
        derivative_url="https://upload.wikimedia.org/Portrait.jpg",
        source_url="https://commons.wikimedia.org/wiki/File:Portrait.jpg",
        license_id="CC_BY_4_0",
        creator="Example Artist",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_text="Example Artist — CC BY 4.0 — Wikimedia Commons",
    )
