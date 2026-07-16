from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from pathlib import Path

import pytest
from webwoven_pipeline.commons_assets import CommonsAssetError, acquire_commons_assets
from webwoven_pipeline.commons_merge import merge_complete_commons_bundles
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


def test_merge_combines_verified_acquisition_and_repair_packs(tmp_path: Path) -> None:
    candidates = {"Q1": "One.jpg", "Q2": "Two.jpg"}
    first = _acquire(candidates, ("Q1",), tmp_path / "first")
    repair = _acquire(candidates, ("Q2",), tmp_path / "repair")

    merged = merge_complete_commons_bundles(
        (first, repair),
        tmp_path / "merged",
        candidates=candidates,
        entity_ids=candidates,
    )

    assert merged.file_by_entity == candidates
    assert len(merged.assets) == 2
    manifest = json.loads(merged.manifest_path.read_text(encoding="utf-8"))
    assert manifest["rejections"] == []
    assert manifest["coverage"]["published_entities"] == 2


def test_merge_rejects_incomplete_repair_coverage(tmp_path: Path) -> None:
    first = _acquire({"Q1": "One.jpg"}, ("Q1",), tmp_path / "first")

    with pytest.raises(CommonsAssetError, match="coverage incomplete for 1 entities"):
        merge_complete_commons_bundles(
            (first,),
            tmp_path / "merged",
            candidates={"Q1": "One.jpg", "Q2": "Two.jpg"},
            entity_ids=("Q1", "Q2"),
        )


def _acquire(candidates: Mapping[str, str], entity_ids: Iterable[str], output: Path):
    return acquire_commons_assets(
        candidates,
        entity_ids,
        output,
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=MetadataClient(),
        binary_transport=BinaryTransport(),
        download_interval=0,
    )


def _record() -> MediaRecord:
    return MediaRecord(
        file_name="Portrait.jpg",
        original_url="https://upload.wikimedia.org/portrait.jpg",
        derivative_url="https://upload.wikimedia.org/portrait-1200.jpg",
        source_url="https://commons.wikimedia.org/wiki/File:Portrait.jpg",
        license_id="CC_BY_4_0",
        creator="Example Artist",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_text="Example Artist — CC BY 4.0 — Wikimedia Commons",
    )
