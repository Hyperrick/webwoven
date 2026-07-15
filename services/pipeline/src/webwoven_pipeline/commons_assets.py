from __future__ import annotations

import hashlib
import json
import shutil
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from .commons import CANONICAL_LICENSE_URLS, CommonsClient
from .http_transport import BinaryResponse, BinaryTransport, UrllibBinaryTransport
from .models import Entity, MediaRecord

MEDIA_MANIFEST_VERSION = 2
MAX_MEDIA_BYTES = 12 * 1024 * 1024
_CONTENT_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class CommonsAssetError(ValueError):
    """Raised when a Commons media pack is malformed or unsafe."""


class CommonsDownloadError(RuntimeError):
    """Raised when a Commons derivative remains unavailable after bounded retries."""


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
    endpoint_ids: Iterable[str],
    destination: Path,
    *,
    user_agent: str,
    created_at: str,
    metadata_client: MetadataClient | None = None,
    binary_transport: BinaryTransport | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    download_interval: float = 0.25,
    max_download_retries: int = 4,
) -> CommonsMediaBundle:
    """Fetch allowlisted endpoint media into a new immutable local media pack."""
    if destination.exists():
        raise FileExistsError(f"refusing to replace Commons media pack: {destination}")
    if download_interval < 0 or max_download_retries < 0:
        raise ValueError("Commons download pacing and retries cannot be negative")
    endpoint_values = set(endpoint_ids)
    selected = {
        qid: candidates[qid]
        for qid in sorted(endpoint_values, key=_qid_number)
        if qid in candidates
    }
    if not selected:
        raise CommonsAssetError("no curated endpoints have Commons media candidates")

    client = metadata_client or CommonsClient(user_agent)
    transport = binary_transport or UrllibBinaryTransport()
    records = client.fetch_metadata(selected.values())
    destination.mkdir(parents=True)
    assets_dir = destination / "assets"
    assets_dir.mkdir()
    assets: dict[str, CommonsAsset] = {}
    rejections: list[dict[str, str]] = []
    try:
        requested_files = set(selected.values())
        rejections.extend(
            {"file_name": file_name, "reason": "metadata_or_license_rejected"}
            for file_name in sorted(requested_files - records.keys())
        )
        for file_name, record in sorted(records.items()):
            if file_name not in requested_files:
                continue
            try:
                derivative_url = _required_upload_url(record.derivative_url)
                response = _download_with_retry(
                    transport,
                    derivative_url,
                    user_agent=user_agent,
                    sleeper=sleeper,
                    interval=download_interval,
                    max_retries=max_download_retries,
                )
                _required_upload_url(response.final_url)
                asset = _store_asset(assets_dir, record, response, created_at)
                assets[file_name] = asset
            except ValueError as exc:
                rejections.append({"file_name": file_name, "reason": type(exc).__name__})
        if not assets:
            raise CommonsAssetError("no Commons candidates passed metadata and binary validation")

        entity_files = tuple(
            (qid, file_name) for qid, file_name in selected.items() if file_name in assets
        )
        manifest_path = destination / "media-manifest.json"
        payload = {
            "version": MEDIA_MANIFEST_VERSION,
            "created_at": created_at,
            "policy": {
                "licenses": ["PUBLIC_DOMAIN", "CC0_1_0", "CC_BY_4_0"],
                "max_bytes": MAX_MEDIA_BYTES,
                "review": "automatic_allowlist",
            },
            "entities": [
                {"entity_id": qid, "file_name": file_name} for qid, file_name in entity_files
            ],
            "assets": [_asset_dict(asset) for asset in assets.values()],
            "rejections": sorted(rejections, key=lambda item: item["file_name"]),
            "coverage": {
                "requested_endpoints": len(endpoint_values),
                "candidate_endpoints": len(selected),
                "published_endpoints": len(entity_files),
                "unique_assets": len(assets),
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
        enriched.append(
            replace(
                entity,
                image_path=asset.public_path,
                image_attribution=asset.record.to_dict(),
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


def _download_with_retry(
    transport: BinaryTransport,
    url: str,
    *,
    user_agent: str,
    sleeper: Callable[[float], None],
    interval: float,
    max_retries: int,
) -> BinaryResponse:
    attempts = max_retries + 1
    for attempt in range(attempts):
        try:
            response = transport.get_bytes(
                url,
                headers={"User-Agent": user_agent, "Accept": "image/webp,image/png,image/jpeg"},
                timeout=45.0,
                max_bytes=MAX_MEDIA_BYTES,
            )
            if interval:
                sleeper(interval)
            return response
        except (HTTPError, URLError, TimeoutError) as exc:
            retryable = not isinstance(exc, HTTPError) or exc.code in {
                429,
                500,
                502,
                503,
                504,
            }
            if not retryable or attempt == attempts - 1:
                raise CommonsDownloadError(
                    f"Commons derivative failed after {attempt + 1} attempts"
                ) from exc
            sleeper(_retry_delay(exc, attempt))
    raise AssertionError("Commons retry loop did not return or raise")


def _retry_delay(error: OSError, attempt: int) -> float:
    header_value = error.headers.get("Retry-After") if isinstance(error, HTTPError) else None
    try:
        retry_after = float(header_value) if header_value is not None else 0.0
    except ValueError:
        retry_after = 0.0
    return min(max(2**attempt, retry_after), 30.0)


def _parse_asset(value: dict[str, Any], root: Path) -> CommonsAsset:
    policy_evidence_value = value.get("policy_evidence")
    if not isinstance(policy_evidence_value, dict):
        raise CommonsAssetError("Commons asset must include policy evidence")
    policy_evidence = cast(dict[str, Any], policy_evidence_value)
    restrictions = _required_string_allow_empty(policy_evidence, "restrictions")
    if restrictions:
        raise CommonsAssetError("Commons asset has source restrictions")
    explicit_attribution = _required_string_allow_empty(policy_evidence, "explicit_attribution")
    record = MediaRecord(
        file_name=_required_string(value, "file_name"),
        original_url=_required_host_url(value, "original_url", "upload.wikimedia.org"),
        derivative_url=_required_host_url(value, "derivative_url", "upload.wikimedia.org"),
        source_url=_required_host_url(value, "source_url", "commons.wikimedia.org"),
        license_id=_required_string(value, "license_id"),
        creator=_required_string(value, "creator"),
        license_url=_required_host_url(value, "license_url", "creativecommons.org"),
        attribution_text=_required_string(value, "attribution_text"),
        restrictions=restrictions,
        explicit_attribution=explicit_attribution,
    )
    if record.license_id not in {"PUBLIC_DOMAIN", "CC0_1_0", "CC_BY_4_0"}:
        raise CommonsAssetError("Commons asset has an unsupported license")
    if record.license_url != CANONICAL_LICENSE_URLS[record.license_id]:
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
    readable_license = {
        "PUBLIC_DOMAIN": "Public Domain",
        "CC0_1_0": "CC0 1.0",
        "CC_BY_4_0": "CC BY 4.0",
    }[record.license_id]
    return f"{credit} — {readable_license} — Wikimedia Commons"


def _storage_note(record: MediaRecord) -> str:
    if record.derivative_url == record.original_url:
        return "Original Commons file stored without local edits"
    return "Commons 1200 px derivative stored without local edits"


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


def _required_upload_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "upload.wikimedia.org":
        raise CommonsAssetError("Commons derivative must use upload.wikimedia.org over HTTPS")
    return value


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
