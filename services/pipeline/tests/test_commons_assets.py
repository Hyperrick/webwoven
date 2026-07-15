from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
from webwoven_pipeline.commons_assets import (
    CommonsAssetError,
    acquire_commons_assets,
    commons_attribution_records,
    copy_commons_assets,
    enrich_entities_with_commons,
    load_commons_media_bundle,
)
from webwoven_pipeline.compiler import GraphCompileError, compile_graph
from webwoven_pipeline.http_transport import BinaryResponse
from webwoven_pipeline.models import Entity, MediaRecord


class FixtureMetadataClient:
    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        assert set(file_names) == {"Portrait.jpg"}
        return {"Portrait.jpg": _record()}


class PartiallyAcceptedMetadataClient:
    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        assert set(file_names) == {"Portrait.jpg", "Rejected.jpg"}
        return {"Portrait.jpg": _record()}


class FixtureBinaryTransport:
    def get_bytes(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
    ) -> BinaryResponse:
        assert url == "https://upload.wikimedia.org/portrait-1200.jpg"
        assert headers["User-Agent"] == "webwoven tests"
        assert timeout == 45.0
        assert max_bytes > 1_000_000
        return BinaryResponse(
            body=b"\xff\xd8\xfffixture-jpeg",
            content_type="image/jpeg",
            final_url=url,
        )


class RedirectedBinaryTransport(FixtureBinaryTransport):
    def get_bytes(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
    ) -> BinaryResponse:
        response = super().get_bytes(
            url,
            headers=headers,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        return BinaryResponse(
            body=response.body,
            content_type=response.content_type,
            final_url="https://example.test/untrusted.jpg",
        )


class RateLimitedBinaryTransport(FixtureBinaryTransport):
    def __init__(self) -> None:
        self.calls = 0

    def get_bytes(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
    ) -> BinaryResponse:
        self.calls += 1
        if self.calls == 1:
            retry_headers = Message()
            retry_headers["Retry-After"] = "3"
            raise HTTPError(url, 429, "rate limited", retry_headers, None)
        return super().get_bytes(
            url,
            headers=headers,
            timeout=timeout,
            max_bytes=max_bytes,
        )


def test_acquire_enrich_copy_and_attribute_commons_assets(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg", "Q2": "Unused.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )

    assert bundle.file_by_entity == {"Q1": "Portrait.jpg"}
    asset = bundle.assets[0]
    assert asset.public_path.startswith("/api/v1/media/")
    assert asset.remote_sha256 == asset.local_sha256
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    assert manifest["coverage"] == {
        "requested_endpoints": 1,
        "candidate_endpoints": 1,
        "published_endpoints": 1,
        "unique_assets": 1,
    }

    entities = (
        Entity("Q1", "One", "First", "wikidata_item", "history_people"),
        Entity("Q2", "Two", "Second", "wikidata_item", "places"),
    )
    enriched = enrich_entities_with_commons(entities, bundle)
    assert enriched[0].image_path == asset.public_path
    assert enriched[0].image_attribution == _record().to_dict()
    assert enriched[1].image_path is None

    destination = tmp_path / "bundle"
    destination.mkdir()
    copied = copy_commons_assets(bundle, destination)
    assert len(copied) == 1
    assert copied[0].read_bytes() == b"\xff\xd8\xfffixture-jpeg"
    attribution = commons_attribution_records(bundle)
    assert attribution[0]["entity_ids"] == ["Q1"]
    assert attribution[0]["policy_evidence"] == {
        "restrictions": "",
        "explicit_attribution": "",
    }
    assert attribution[0]["modifications"] == [
        "Commons 1200 px derivative stored without local edits"
    ]
    assert attribution[0]["review_status"] == "automatic_allowlist_passed"

    original_record = replace(asset.record, derivative_url=asset.record.original_url)
    original_bundle = replace(
        bundle,
        assets=(replace(asset, record=original_record),),
    )
    original_attribution = commons_attribution_records(original_bundle)
    assert original_attribution[0]["modifications"] == [
        "Original Commons file stored without local edits"
    ]


def test_loader_rejects_a_tampered_local_asset(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )
    asset_path = bundle.manifest_path.parent / bundle.assets[0].asset_path
    asset_path.write_bytes(b"changed")

    with pytest.raises(CommonsAssetError, match="does not match"):
        load_commons_media_bundle(bundle.manifest_path)


def test_acquisition_records_metadata_and_license_rejections(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg", "Q2": "Rejected.jpg"},
        ("Q1", "Q2"),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=PartiallyAcceptedMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )

    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    assert manifest["rejections"] == [
        {"file_name": "Rejected.jpg", "reason": "metadata_or_license_rejected"}
    ]
    assert manifest["coverage"]["candidate_endpoints"] == 2
    assert manifest["coverage"]["published_endpoints"] == 1


def test_loader_rejects_self_consistent_non_image_bytes(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    old_path = bundle.manifest_path.parent / manifest["assets"][0]["asset_path"]
    old_path.unlink()
    body = b"this is not a JPEG"
    digest = hashlib.sha256(body).hexdigest()
    new_path = old_path.parent / f"{digest}.jpg"
    new_path.write_bytes(body)
    manifest["assets"][0].update(
        {
            "asset_path": f"assets/{new_path.name}",
            "public_path": f"/api/v1/media/{new_path.name}",
            "bytes": len(body),
            "remote_sha256": digest,
            "local_sha256": digest,
        }
    )
    bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CommonsAssetError, match="content does not match"):
        load_commons_media_bundle(bundle.manifest_path)


def test_loader_rejects_a_license_url_that_disagrees_with_the_license(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    manifest["assets"][0]["license_url"] = "https://creativecommons.org/licenses/by-sa/4.0/"
    bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CommonsAssetError, match="license URL does not match"):
        load_commons_media_bundle(bundle.manifest_path)


def test_loader_rejects_stale_or_tampered_policy_evidence(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = 1
    bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CommonsAssetError, match="unsupported Commons media manifest"):
        load_commons_media_bundle(bundle.manifest_path)

    manifest["version"] = 2
    manifest["assets"][0]["policy_evidence"]["restrictions"] = "trademarked"
    bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CommonsAssetError, match="source restrictions"):
        load_commons_media_bundle(bundle.manifest_path)


def test_loader_rejects_attribution_that_omits_required_credit(tmp_path: Path) -> None:
    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=FixtureBinaryTransport(),
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    manifest["assets"][0]["attribution_text"] = "Some credit — CC BY 4.0"
    bundle.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CommonsAssetError, match="attribution text is incomplete"):
        load_commons_media_bundle(bundle.manifest_path)


def test_acquisition_rejects_a_derivative_redirected_off_wikimedia(tmp_path: Path) -> None:
    with pytest.raises(CommonsAssetError, match="no Commons candidates"):
        acquire_commons_assets(
            {"Q1": "Portrait.jpg"},
            ("Q1",),
            tmp_path / "acquired",
            user_agent="webwoven tests",
            created_at="2026-07-15T12:00:00Z",
            metadata_client=FixtureMetadataClient(),
            binary_transport=RedirectedBinaryTransport(),
        )


def test_acquisition_retries_rate_limits_and_preserves_request_pacing(tmp_path: Path) -> None:
    transport = RateLimitedBinaryTransport()
    sleeps: list[float] = []

    bundle = acquire_commons_assets(
        {"Q1": "Portrait.jpg"},
        ("Q1",),
        tmp_path / "acquired",
        user_agent="webwoven tests",
        created_at="2026-07-15T12:00:00Z",
        metadata_client=FixtureMetadataClient(),
        binary_transport=transport,
        sleeper=sleeps.append,
    )

    assert len(bundle.assets) == 1
    assert transport.calls == 2
    assert sleeps == [3.0, 0.25]


def test_compiler_rejects_unattributed_media(tmp_path: Path, registry) -> None:
    entity = Entity(
        "Q1",
        "One",
        "First",
        "wikidata_item",
        "history_people",
        image_path="/api/v1/media/" + "a" * 64 + ".jpg",
    )

    with pytest.raises(GraphCompileError, match="pair every image"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (entity,), (), ())


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
