from __future__ import annotations

import hashlib
import json
import shutil
import time
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import parse_qs, urlencode, urlparse

from .commons import CommonsClient, matches_license_url
from .commons_asset_reuse import materialize_reused_assets
from .commons_downloads import CommonsDownloadError, DownloadPacer, download_with_fallback
from .http_transport import BinaryResponse, BinaryTransport, HttpxBinaryTransport
from .media_licenses import SUPPORTED_LICENSE_IDS, license_spec
from .models import Entity, MediaRecord

MEDIA_MANIFEST_VERSION = 3
MAX_MEDIA_BYTES = 12 * 1024 * 1024
DISPLAY_DERIVATIVE_WIDTH = 640
ANIMATED_DISPLAY_DERIVATIVE_WIDTH = 480
DISPLAY_DERIVATIVE_WIDTHS = {
    DISPLAY_DERIVATIVE_WIDTH,
    ANIMATED_DISPLAY_DERIVATIVE_WIDTH,
}
_CONTENT_EXTENSIONS = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class CommonsAssetError(ValueError):
    """Raised when a Commons media pack is malformed or unsafe."""


class MetadataClient(Protocol):
    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]: ...


@dataclass(frozen=True, slots=True)
class CommonsAsset:
    record: MediaRecord
    asset_path: str
    public_path: str
    content_type: str
    byte_count: int
    remote_sha256: str
    local_sha256: str
    retrieved_at: str
    review_status: str


@dataclass(frozen=True, slots=True)
class CommonsMediaBundle:
    manifest_path: Path
    created_at: str
    assets: tuple[CommonsAsset, ...]
    entity_files: tuple[tuple[str, str], ...]

    @property
    def assets_by_file(self) -> dict[str, CommonsAsset]:
        return {asset.record.file_name: asset for asset in self.assets}

    @property
    def file_by_entity(self) -> dict[str, str]:
        return dict(self.entity_files)


def acquire_commons_assets(
    candidates: Mapping[str, str],
    entity_ids: Iterable[str],
    destination: Path,
    *,
    user_agent: str,
    created_at: str,
    metadata_client: MetadataClient | None = None,
    binary_transport: BinaryTransport | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    download_interval: float = 1.0,
    max_download_retries: int = 8,
    require_complete: bool = False,
    download_workers: int = 1,
    reuse_bundle: CommonsMediaBundle | None = None,
) -> CommonsMediaBundle:
    """Fetch allowlisted entity media into a new immutable local media pack."""
    if destination.exists():
        raise FileExistsError(f"refusing to replace Commons media pack: {destination}")
    if download_interval < 0 or max_download_retries < 0:
        raise ValueError("Commons download pacing and retries cannot be negative")
    if not 1 <= download_workers <= 16:
        raise ValueError("Commons download workers must be between 1 and 16")
    entity_values = set(entity_ids)
    selected = {
        qid: candidates[qid] for qid in sorted(entity_values, key=_qid_number) if qid in candidates
    }
    if not selected:
        raise CommonsAssetError("no graph entities have Commons media candidates")

    reusable = {
        file_name: asset
        for file_name, asset in (reuse_bundle.assets_by_file if reuse_bundle else {}).items()
        if file_name in selected.values()
    }
    new_files = set(selected.values()) - reusable.keys()
    client = metadata_client or CommonsClient(
        user_agent,
        request_interval=max(download_interval, 0.25),
    )
    transport = binary_transport or HttpxBinaryTransport()
    records = {
        **{file_name: asset.record for file_name, asset in reusable.items()},
        **client.fetch_metadata(new_files),
    }
    destination.mkdir(parents=True)
    assets_dir = destination / "assets"
    assets_dir.mkdir()
    assets: dict[str, CommonsAsset] = {}
    rejections: list[dict[str, str]] = []
    try:
        if reuse_bundle is not None:
            assets.update(
                materialize_reused_assets(
                    reuse_bundle.manifest_path.parent,
                    destination,
                    reusable,
                )
            )
        requested_files = set(selected.values())
        rejections.extend(
            {"file_name": file_name, "reason": "metadata_or_license_rejected"}
            for file_name in sorted(requested_files - records.keys())
        )
        downloadable = {
            file_name: _display_derivative(record)
            for file_name, record in sorted(records.items())
            if file_name in new_files
        }
        pacer = (
            DownloadPacer(download_interval, sleeper)
            if download_workers > 1 and download_interval
            else None
        )
        with ThreadPoolExecutor(max_workers=download_workers) as executor:
            futures = {
                executor.submit(
                    download_with_fallback,
                    transport,
                    _required_derivative_url(record.derivative_url),
                    _required_derivative_url(record.original_url),
                    user_agent=user_agent,
                    sleeper=sleeper,
                    interval=download_interval,
                    max_retries=max_download_retries,
                    max_bytes=MAX_MEDIA_BYTES,
                    pacer=pacer,
                ): (file_name, record)
                for file_name, record in downloadable.items()
            }
            for future in as_completed(futures):
                file_name, record = futures[future]
                try:
                    downloaded_url, response = future.result()
                    _required_derivative_url(response.final_url)
                    assets[file_name] = _store_asset(
                        assets_dir,
                        replace(record, derivative_url=downloaded_url),
                        response,
                        created_at,
                    )
                except (ValueError, CommonsDownloadError) as exc:
                    rejections.append({"file_name": file_name, "reason": type(exc).__name__})
        if not assets:
            raise CommonsAssetError("no Commons candidates passed metadata and binary validation")

        entity_files = tuple(
            (qid, file_name) for qid, file_name in selected.items() if file_name in assets
        )
        if require_complete and len(entity_files) != len(entity_values):
            missing = sorted(entity_values - {qid for qid, _ in entity_files}, key=_qid_number)
            raise CommonsAssetError(
                f"Commons media coverage incomplete for {len(missing)} entities; "
                f"first missing: {', '.join(missing[:10])}"
            )
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
                {"entity_id": qid, "file_name": file_name} for qid, file_name in entity_files
            ],
            "assets": [_asset_dict(assets[file_name]) for file_name in sorted(assets)],
            "rejections": sorted(rejections, key=lambda item: item["file_name"]),
            "coverage": {
                "requested_entities": len(entity_values),
                "candidate_entities": len(selected),
                "published_entities": len(entity_files),
                "unique_assets": len(assets),
                "reused_assets": len(reusable),
                "downloaded_assets": len(assets) - len(reusable),
            },
        }
        _write_json(manifest_path, payload)
        return load_commons_media_bundle(manifest_path)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def load_commons_media_bundle(manifest_path: Path) -> CommonsMediaBundle:
    value: object = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CommonsAssetError("Commons media manifest must be an object")
    payload = cast(dict[str, Any], value)
    if payload.get("version") != MEDIA_MANIFEST_VERSION:
        raise CommonsAssetError("unsupported Commons media manifest version")
    created_at = _required_string(payload, "created_at")
    assets = tuple(
        _parse_asset(item, manifest_path.parent)
        for item in _object_list(payload.get("assets"), "assets")
    )
    if not assets:
        raise CommonsAssetError("Commons media manifest has no assets")
    assets_by_file = {asset.record.file_name: asset for asset in assets}
    if len(assets_by_file) != len(assets):
        raise CommonsAssetError("Commons media manifest repeats a file name")

    entity_files: list[tuple[str, str]] = []
    seen_entities: set[str] = set()
    for item in _object_list(payload.get("entities"), "entities"):
        entity_id = _required_string(item, "entity_id")
        file_name = _required_string(item, "file_name")
        if entity_id in seen_entities or not _valid_qid(entity_id):
            raise CommonsAssetError("Commons media manifest has an invalid entity mapping")
        if file_name not in assets_by_file:
            raise CommonsAssetError("Commons entity mapping references an unknown asset")
        seen_entities.add(entity_id)
        entity_files.append((entity_id, file_name))
    return CommonsMediaBundle(
        manifest_path=manifest_path,
        created_at=created_at,
        assets=tuple(sorted(assets, key=lambda item: item.record.file_name)),
        entity_files=tuple(sorted(entity_files, key=lambda item: _qid_number(item[0]))),
    )


def enrich_entities_with_commons(
    entities: Iterable[Entity],
    bundle: CommonsMediaBundle,
    selection_sources: Mapping[str, str] | None = None,
) -> tuple[Entity, ...]:
    assets = bundle.assets_by_file
    entity_files = bundle.file_by_entity
    enriched: list[Entity] = []
    for entity in entities:
        file_name = entity_files.get(entity.id)
        asset = assets.get(file_name) if file_name else None
        if asset is None:
            enriched.append(entity)
            continue
        attribution = asset.record.to_dict()
        context_label = media_context_label((selection_sources or {}).get(entity.id))
        if context_label is not None:
            attribution["context_label"] = context_label
        enriched.append(
            replace(
                entity,
                image_path=asset.public_path,
                image_attribution=attribution,
            )
        )
    return tuple(enriched)


def copy_commons_assets(
    bundle: CommonsMediaBundle,
    destination: Path,
) -> tuple[Path, ...]:
    media_dir = destination / "media"
    media_dir.mkdir()
    copied: dict[str, Path] = {}
    for asset in bundle.assets:
        source = bundle.manifest_path.parent / asset.asset_path
        target = media_dir / Path(asset.asset_path).name
        if not target.exists():
            shutil.copyfile(source, target)
        if _sha256(target) != asset.local_sha256:
            raise CommonsAssetError(f"copied Commons asset hash mismatch: {target.name}")
        copied[target.name] = target
    return tuple(copied[name] for name in sorted(copied))


def commons_attribution_records(bundle: CommonsMediaBundle) -> list[dict[str, Any]]:
    entity_ids_by_file: dict[str, list[str]] = {}
    for entity_id, file_name in bundle.entity_files:
        entity_ids_by_file.setdefault(file_name, []).append(entity_id)
    return [
        {
            **asset.record.to_dict(),
            "policy_evidence": asset.record.policy_evidence(),
            "entity_ids": entity_ids_by_file.get(asset.record.file_name, []),
            "local_path": f"media/{Path(asset.asset_path).name}",
            "public_path": asset.public_path,
            "content_type": asset.content_type,
            "bytes": asset.byte_count,
            "remote_sha256": asset.remote_sha256,
            "local_sha256": asset.local_sha256,
            "retrieved_at": asset.retrieved_at,
            "modifications": [_storage_note(asset.record)],
            "review_status": asset.review_status,
        }
        for asset in bundle.assets
    ]


def _store_asset(
    assets_dir: Path,
    record: MediaRecord,
    response: BinaryResponse,
    retrieved_at: str,
) -> CommonsAsset:
    extension = _CONTENT_EXTENSIONS.get(response.content_type)
    if extension is None or not _matches_signature(response):
        raise CommonsAssetError("Commons derivative is not a supported raster image")
    digest = hashlib.sha256(response.body).hexdigest()
    relative = f"assets/{digest}{extension}"
    asset_path = assets_dir.parent / relative
    if asset_path.exists() and _sha256(asset_path) != digest:
        raise CommonsAssetError("Commons asset hash collision")
    if not asset_path.exists():
        asset_path.write_bytes(response.body)
    return CommonsAsset(
        record=record,
        asset_path=relative,
        public_path=f"/api/v1/media/{asset_path.name}",
        content_type=response.content_type,
        byte_count=len(response.body),
        remote_sha256=digest,
        local_sha256=digest,
        retrieved_at=retrieved_at,
        review_status="automatic_allowlist_passed",
    )


def _parse_asset(value: dict[str, Any], root: Path) -> CommonsAsset:
    policy_evidence_value = value.get("policy_evidence")
    if not isinstance(policy_evidence_value, dict):
        raise CommonsAssetError("Commons asset must include policy evidence")
    policy_evidence = cast(dict[str, Any], policy_evidence_value)
    restrictions = _required_string_allow_empty(policy_evidence, "restrictions")
    explicit_attribution = _required_string_allow_empty(policy_evidence, "explicit_attribution")
    record = MediaRecord(
        file_name=_required_string(value, "file_name"),
        original_url=_required_host_url(value, "original_url", "upload.wikimedia.org"),
        derivative_url=_required_derivative_url(_required_string(value, "derivative_url")),
        source_url=_required_host_url(value, "source_url", "commons.wikimedia.org"),
        license_id=_required_string(value, "license_id"),
        creator=_required_string(value, "creator"),
        license_url=_required_host_url(value, "license_url", "creativecommons.org"),
        attribution_text=_required_string(value, "attribution_text"),
        restrictions=restrictions,
        explicit_attribution=explicit_attribution,
    )
    if record.license_id not in SUPPORTED_LICENSE_IDS:
        raise CommonsAssetError("Commons asset has an unsupported license")
    if not matches_license_url(record.license_url, record.license_id):
        raise CommonsAssetError("Commons asset license URL does not match its license")
    if record.attribution_text != _expected_attribution_text(record):
        raise CommonsAssetError("Commons asset attribution text is incomplete")
    asset_path = _safe_relative_path(_required_string(value, "asset_path"))
    public_path = _required_string(value, "public_path")
    if public_path != f"/api/v1/media/{Path(asset_path).name}":
        raise CommonsAssetError("Commons asset public path does not match its local file")
    path = root / asset_path
    byte_count = _required_integer(value, "bytes")
    remote_sha256 = _required_hash(value, "remote_sha256")
    local_sha256 = _required_hash(value, "local_sha256")
    if remote_sha256 != local_sha256:
        raise CommonsAssetError(
            "unmodified Commons assets require matching remote and local hashes"
        )
    content_type = _required_string(value, "content_type")
    expected_extension = _CONTENT_EXTENSIONS.get(content_type)
    if expected_extension is None or Path(asset_path).suffix != expected_extension:
        raise CommonsAssetError("Commons asset type does not match its local file")
    if not path.is_file() or path.stat().st_size != byte_count or _sha256(path) != local_sha256:
        raise CommonsAssetError(f"Commons asset does not match its manifest: {asset_path}")
    if not _matches_file_signature(path, content_type):
        raise CommonsAssetError("Commons asset content does not match its declared type")
    return CommonsAsset(
        record=record,
        asset_path=asset_path,
        public_path=public_path,
        content_type=content_type,
        byte_count=byte_count,
        remote_sha256=remote_sha256,
        local_sha256=local_sha256,
        retrieved_at=_required_string(value, "retrieved_at"),
        review_status=_review_status(value),
    )


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


def _matches_signature(response: BinaryResponse) -> bool:
    body = response.body
    if response.content_type == "image/jpeg":
        return body.startswith(b"\xff\xd8\xff")
    if response.content_type == "image/png":
        return body.startswith(b"\x89PNG\r\n\x1a\n")
    if response.content_type == "image/webp":
        return len(body) >= 12 and body.startswith(b"RIFF") and body[8:12] == b"WEBP"
    if response.content_type == "image/gif":
        return body.startswith((b"GIF87a", b"GIF89a"))
    return False


def _matches_file_signature(path: Path, content_type: str) -> bool:
    with path.open("rb") as handle:
        prefix = handle.read(12)
    return _matches_signature(
        BinaryResponse(
            body=prefix,
            content_type=content_type,
            final_url="https://upload.wikimedia.org/",
        )
    )


def _object_list(value: object, name: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise CommonsAssetError(f"{name} must be a list")
    items: list[dict[str, Any]] = []
    for item in cast(list[Any], value):
        if not isinstance(item, dict):
            raise CommonsAssetError(f"every {name} item must be an object")
        items.append(cast(dict[str, Any], item))
    return tuple(items)


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise CommonsAssetError(f"{key} must be a non-empty string")
    return item


def _required_string_allow_empty(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise CommonsAssetError(f"{key} must be a string")
    return item


def _expected_attribution_text(record: MediaRecord) -> str:
    credit = record.creator
    if record.explicit_attribution:
        credit = (
            record.explicit_attribution
            if record.creator.casefold() in record.explicit_attribution.casefold()
            else f"{record.explicit_attribution} · {record.creator}"
        )
    spec = license_spec(record.license_id)
    if spec is None:
        raise CommonsAssetError("Commons asset has an unsupported license")
    return f"{credit} — {spec.label} — Wikimedia Commons"


def _storage_note(record: MediaRecord) -> str:
    if record.derivative_url == record.original_url:
        return "Original Commons file stored without local edits"
    return "Commons display derivative stored without local edits"


def media_context_label(selection_source: str | None) -> str | None:
    if not selection_source or not selection_source.startswith("graph_context:"):
        return None
    parts = selection_source.split(":", 3)
    return parts[3] if len(parts) == 4 and parts[3].strip() else None


def _required_integer(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if not isinstance(item, int) or item < 1:
        raise CommonsAssetError(f"{key} must be a positive integer")
    return item


def _required_host_url(value: Mapping[str, Any], key: str, host: str) -> str:
    item = _required_string(value, key)
    parsed = urlparse(item)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise CommonsAssetError(f"{key} must use {host} over HTTPS")
    return item


def _required_derivative_url(value: str) -> str:
    parsed = urlparse(value)
    upload_url = parsed.scheme == "https" and parsed.hostname == "upload.wikimedia.org"
    query = parse_qs(parsed.query, strict_parsing=True)
    official_thumbnail = (
        parsed.scheme == "https"
        and parsed.hostname == "commons.wikimedia.org"
        and parsed.path == "/w/thumb.php"
        and set(query) == {"f", "w"}
        and len(query["f"]) == 1
        and bool(query["f"][0].strip())
        and len(query["w"]) == 1
        and query["w"][0].isdigit()
        and int(query["w"][0]) in DISPLAY_DERIVATIVE_WIDTHS
    )
    if not upload_url and not official_thumbnail:
        raise CommonsAssetError("Commons derivative must use an approved Wikimedia HTTPS URL")
    return value


def _display_derivative(record: MediaRecord) -> MediaRecord:
    if record.derivative_url != record.original_url:
        return record
    width = (
        ANIMATED_DISPLAY_DERIVATIVE_WIDTH
        if record.file_name.casefold().endswith(".gif")
        else DISPLAY_DERIVATIVE_WIDTH
    )
    query = urlencode({"f": record.file_name, "w": str(width)})
    return replace(record, derivative_url=f"https://commons.wikimedia.org/w/thumb.php?{query}")


def _review_status(value: Mapping[str, Any]) -> str:
    status = _required_string(value, "review_status")
    if status != "automatic_allowlist_passed":
        raise CommonsAssetError("Commons asset has not passed the automatic allowlist")
    return status


def _required_hash(value: Mapping[str, Any], key: str) -> str:
    item = _required_string(value, key)
    if len(item) != 64 or any(character not in "0123456789abcdef" for character in item):
        raise CommonsAssetError(f"{key} must be a lowercase SHA-256 hash")
    return item


def _safe_relative_path(value: str) -> str:
    path = Path(value)
    unsafe = (
        path.is_absolute()
        or ".." in path.parts
        or len(path.parts) != 2
        or path.parts[0] != "assets"
    )
    if unsafe:
        raise CommonsAssetError("asset_path must be a safe path below assets/")
    return path.as_posix()


def _valid_qid(value: str) -> bool:
    return value.startswith("Q") and value[1:].isdigit() and value[1] != "0"


def _qid_number(value: str) -> int:
    if not _valid_qid(value):
        raise CommonsAssetError(f"invalid Wikidata entity ID: {value}")
    return int(value[1:])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
