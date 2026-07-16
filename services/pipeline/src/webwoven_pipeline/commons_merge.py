from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .commons_assets import (
    MAX_MEDIA_BYTES,
    MEDIA_MANIFEST_VERSION,
    CommonsAsset,
    CommonsAssetError,
    CommonsMediaBundle,
    load_commons_media_bundle,
)
from .media_licenses import SUPPORTED_LICENSE_IDS


def merge_complete_commons_bundles(
    bundles: Iterable[CommonsMediaBundle],
    destination: Path,
    *,
    candidates: Mapping[str, str],
    entity_ids: Iterable[str],
) -> CommonsMediaBundle:
    """Merge verified acquisition and repair packs into one complete immutable pack."""
    if destination.exists():
        raise FileExistsError(f"refusing to replace Commons media pack: {destination}")
    bundle_values = tuple(bundles)
    if not bundle_values:
        raise CommonsAssetError("at least one Commons media bundle is required")
    created_at = bundle_values[0].created_at
    if any(bundle.created_at != created_at for bundle in bundle_values):
        raise CommonsAssetError("Commons media bundles must share one snapshot timestamp")

    expected_entities = set(entity_ids)
    if not expected_entities or any(qid not in candidates for qid in expected_entities):
        raise CommonsAssetError("every expected graph entity needs a media candidate")

    assets: dict[str, tuple[CommonsAsset, Path]] = {}
    entity_files: dict[str, str] = {}
    for bundle in bundle_values:
        root = bundle.manifest_path.parent
        for asset in bundle.assets:
            existing = assets.get(asset.record.file_name)
            if existing is not None and _asset_identity(existing[0]) != _asset_identity(asset):
                raise CommonsAssetError("Commons repair bundle conflicts with an existing asset")
            assets.setdefault(asset.record.file_name, (asset, root))
        for entity_id, file_name in bundle.entity_files:
            if entity_id not in expected_entities or candidates.get(entity_id) != file_name:
                raise CommonsAssetError("Commons repair mapping does not match the graph source")
            existing_file = entity_files.get(entity_id)
            if existing_file is not None and existing_file != file_name:
                raise CommonsAssetError("Commons repair bundles conflict on an entity mapping")
            entity_files[entity_id] = file_name

    if set(entity_files) != expected_entities:
        missing = sorted(expected_entities - set(entity_files), key=_qid_number)
        raise CommonsAssetError(
            f"merged Commons media coverage incomplete for {len(missing)} entities; "
            f"first missing: {', '.join(missing[:10])}"
        )
    referenced_files = set(entity_files.values())
    if set(assets) != referenced_files:
        raise CommonsAssetError("merged Commons media assets do not match entity mappings")

    destination.mkdir(parents=True)
    assets_dir = destination / "assets"
    assets_dir.mkdir()
    try:
        for asset, root in assets.values():
            source = root / asset.asset_path
            target = destination / asset.asset_path
            if target.exists():
                continue
            try:
                os.link(source, target)
            except OSError:
                shutil.copyfile(source, target)
        manifest_path = destination / "media-manifest.json"
        payload = {
            "version": MEDIA_MANIFEST_VERSION,
            "created_at": created_at,
            "policy": {
                "licenses": sorted(SUPPORTED_LICENSE_IDS),
                "max_bytes": MAX_MEDIA_BYTES,
                "review": "automatic_allowlist",
            },
            "entities": [
                {"entity_id": qid, "file_name": entity_files[qid]}
                for qid in sorted(entity_files, key=_qid_number)
            ],
            "assets": [_asset_dict(assets[file_name][0]) for file_name in sorted(assets)],
            "rejections": [],
            "coverage": {
                "requested_entities": len(expected_entities),
                "candidate_entities": len(expected_entities),
                "published_entities": len(entity_files),
                "unique_assets": len(assets),
            },
        }
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return load_commons_media_bundle(manifest_path)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def _asset_dict(asset: CommonsAsset) -> dict[str, Any]:
    return {
        **asset.record.to_dict(),
        "policy_evidence": asset.record.policy_evidence(),
        "asset_path": asset.asset_path,
        "public_path": asset.public_path,
        "content_type": asset.content_type,
        "bytes": asset.byte_count,
        "remote_sha256": asset.remote_sha256,
        "local_sha256": asset.local_sha256,
        "retrieved_at": asset.retrieved_at,
        "review_status": asset.review_status,
    }


def _asset_identity(asset: CommonsAsset) -> tuple[object, ...]:
    return (
        asset.record,
        asset.asset_path,
        asset.public_path,
        asset.content_type,
        asset.byte_count,
        asset.remote_sha256,
        asset.local_sha256,
        asset.retrieved_at,
        asset.review_status,
    )


def _qid_number(value: str) -> int:
    if len(value) < 2 or value[0] != "Q" or not value[1:].isdigit():
        raise CommonsAssetError(f"invalid QID: {value}")
    return int(value[1:])
