from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from .commons import CommonsClient
from .commons_discovery import CommonsDiscoveryClient
from .media_context import MediaContextHint, selected_neighbor_media_candidates
from .reviewed_media import ReviewedMediaCandidate
from .wikipedia_media import WikipediaMediaClient

COMMONS_VALIDATION_CACHE_VERSION = 2


class LicenseValidator(Protocol):
    def accepted_files(self, file_names: Iterable[str]) -> set[str]: ...


class DiscoveryCandidate(Protocol):
    @property
    def file_name(self) -> str: ...

    @property
    def provenance(self) -> str: ...


@dataclass(frozen=True, slots=True)
class MediaSelection:
    entity_id: str
    file_name: str
    provenance: str


@dataclass(frozen=True, slots=True)
class MediaDiscoveryResult:
    selections: tuple[MediaSelection, ...]
    missing_entity_ids: tuple[str, ...]
    direct_count: int
    wikipedia_count: int
    category_count: int
    depicts_count: int
    search_count: int
    broad_search_count: int
    wikipedia_article_count: int
    context_count: int
    reviewed_count: int

    @property
    def files_by_entity(self) -> dict[str, str]:
        return {selection.entity_id: selection.file_name for selection in self.selections}

    @property
    def sources_by_entity(self) -> dict[str, str]:
        return {selection.entity_id: selection.provenance for selection in self.selections}


class CommonsLicenseValidator:
    """Cache the allowlist verdicts needed during offline media discovery."""

    def __init__(
        self,
        cache_dir: Path,
        user_agent: str,
        *,
        client: CommonsClient | None = None,
    ) -> None:
        self._cache_dir = cache_dir
        self._client = client or CommonsClient(user_agent)

    def accepted_files(self, file_names: Iterable[str]) -> set[str]:
        normalized = tuple(sorted({_normalize_file_name(name) for name in file_names}))
        accepted: set[str] = set()
        for batch in _chunked(normalized, 50):
            accepted.update(self._accepted_batch(batch))
        return accepted

    def _accepted_batch(self, file_names: tuple[str, ...]) -> set[str]:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / _validation_cache_name(file_names)
        if cache_path.exists():
            return _read_accepted_cache(cache_path, file_names)
        accepted = set(self._client.fetch_metadata(file_names))
        payload = {
            "version": COMMONS_VALIDATION_CACHE_VERSION,
            "requested": list(file_names),
            "accepted": sorted(accepted),
        }
        payload_bytes = _canonical_bytes(payload)
        try:
            with cache_path.open("xb") as handle:
                handle.write(payload_bytes)
        except FileExistsError:
            return _read_accepted_cache(cache_path, file_names)
        return accepted


def discover_media(
    entity_ids: Iterable[str],
    direct_candidates: Mapping[str, str],
    direct_sources: Mapping[str, str],
    wikipedia_sitelinks: Mapping[str, Mapping[str, str]],
    *,
    wikipedia_client: WikipediaMediaClient,
    license_validator: LicenseValidator,
    commons_client: CommonsDiscoveryClient | None = None,
    commons_categories: Mapping[str, str] | None = None,
    entity_labels: Mapping[str, str] | None = None,
    context_hints: Mapping[str, tuple[MediaContextHint, ...]] | None = None,
    reviewed_candidates: Mapping[str, tuple[ReviewedMediaCandidate, ...]] | None = None,
) -> MediaDiscoveryResult:
    """Select the best validated Commons image for each exact graph entity."""
    qids = tuple(sorted(set(entity_ids), key=_qid_number))
    selected: dict[str, MediaSelection] = {}

    normalized_direct = {
        qid: _normalize_file_name(file_name)
        for qid, file_name in direct_candidates.items()
        if qid in set(qids)
    }
    accepted_direct = license_validator.accepted_files(normalized_direct.values())
    for qid in qids:
        file_name = normalized_direct.get(qid)
        if file_name in accepted_direct:
            selected[qid] = MediaSelection(
                qid,
                file_name,
                direct_sources.get(qid, "wikidata_media"),
            )
    direct_count = len(selected)

    unresolved = tuple(qid for qid in qids if qid not in selected)
    lead_candidates = wikipedia_client.fetch_lead_candidates(
        wikipedia_sitelinks,
        entity_ids=unresolved,
    )
    before = len(selected)
    unresolved = _select_validated_candidates(
        unresolved,
        lead_candidates,
        selected,
        license_validator,
    )
    wikipedia_count = len(selected) - before

    category_count = 0
    depicts_count = 0
    search_count = 0
    broad_search_count = 0
    wikipedia_article_count = 0
    context_count = 0
    reviewed_count = 0
    labels = entity_labels or {}
    if commons_client is not None:
        category_candidates = commons_client.fetch_category_candidates(
            unresolved,
            commons_categories or {},
            labels,
        )
        before = len(selected)
        unresolved = _select_validated_candidates(
            unresolved,
            category_candidates,
            selected,
            license_validator,
        )
        category_count = len(selected) - before

        depicts_candidates = commons_client.fetch_depicts_candidates(unresolved, labels)
        before = len(selected)
        unresolved = _select_validated_candidates(
            unresolved,
            depicts_candidates,
            selected,
            license_validator,
        )
        depicts_count = len(selected) - before

        label_candidates = commons_client.fetch_label_candidates(unresolved, labels)
        before = len(selected)
        unresolved = _select_validated_candidates(
            unresolved,
            label_candidates,
            selected,
            license_validator,
        )
        search_count = len(selected) - before

    article_candidates = wikipedia_client.fetch_article_candidates(
        wikipedia_sitelinks,
        labels,
        entity_ids=unresolved,
    )
    before = len(selected)
    unresolved = _select_validated_candidates(
        unresolved,
        article_candidates,
        selected,
        license_validator,
    )
    wikipedia_article_count = len(selected) - before

    if context_hints:
        neighbor_candidates = selected_neighbor_media_candidates(
            unresolved,
            context_hints,
            {qid: selection.file_name for qid, selection in selected.items()},
        )
        before = len(selected)
        unresolved = _select_validated_candidates(
            unresolved,
            neighbor_candidates,
            selected,
            license_validator,
        )
        context_count += len(selected) - before

    if commons_client is not None:
        broad_candidates = commons_client.fetch_broad_candidates(unresolved, labels)
        before = len(selected)
        unresolved = _select_validated_candidates(
            unresolved,
            broad_candidates,
            selected,
            license_validator,
        )
        broad_search_count = len(selected) - before

        context_candidates = commons_client.fetch_context_candidates(
            unresolved,
            context_hints or {},
        )
        before = len(selected)
        unresolved = _select_validated_candidates(
            unresolved,
            context_candidates,
            selected,
            license_validator,
        )
        context_count += len(selected) - before

    before = len(selected)
    unresolved = _select_validated_candidates(
        unresolved,
        reviewed_candidates or {},
        selected,
        license_validator,
    )
    reviewed_count = len(selected) - before

    selections = tuple(selected[qid] for qid in qids if qid in selected)
    return MediaDiscoveryResult(
        selections=selections,
        missing_entity_ids=tuple(qid for qid in qids if qid not in selected),
        direct_count=direct_count,
        wikipedia_count=wikipedia_count,
        category_count=category_count,
        depicts_count=depicts_count,
        search_count=search_count,
        broad_search_count=broad_search_count,
        wikipedia_article_count=wikipedia_article_count,
        context_count=context_count,
        reviewed_count=reviewed_count,
    )


def _select_validated_candidates(
    unresolved: tuple[str, ...],
    candidates_by_qid: Mapping[str, tuple[DiscoveryCandidate, ...]],
    selected: dict[str, MediaSelection],
    license_validator: LicenseValidator,
) -> tuple[str, ...]:
    candidate_index = 0
    while unresolved:
        round_candidates = {
            qid: candidates[candidate_index]
            for qid in unresolved
            if candidate_index < len(candidates := candidates_by_qid.get(qid, ()))
        }
        if not round_candidates:
            break
        accepted = license_validator.accepted_files(
            candidate.file_name for candidate in round_candidates.values()
        )
        for qid, candidate in round_candidates.items():
            normalized = _normalize_file_name(candidate.file_name)
            if normalized in accepted:
                selected[qid] = MediaSelection(qid, normalized, candidate.provenance)
        unresolved = tuple(qid for qid in unresolved if qid not in selected)
        candidate_index += 1
    return unresolved


def _normalize_file_name(value: str) -> str:
    name = value.removeprefix("File:").strip().replace("_", " ")
    if not name:
        raise ValueError("Commons file name cannot be empty")
    return name


def _validation_cache_name(file_names: tuple[str, ...]) -> str:
    digest = hashlib.sha256("\n".join(file_names).encode()).hexdigest()[:20]
    return f"commons-license-v{COMMONS_VALIDATION_CACHE_VERSION}-{len(file_names)}-{digest}.json"


def _read_accepted_cache(path: Path, expected: tuple[str, ...]) -> set[str]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Commons validation cache {path} is not an object")
    payload = cast(dict[str, Any], value)
    if payload.get("version") != COMMONS_VALIDATION_CACHE_VERSION:
        raise ValueError(f"unsupported Commons validation cache: {path}")
    requested = payload.get("requested")
    accepted = payload.get("accepted")
    if requested != list(expected) or not isinstance(accepted, list):
        raise ValueError(f"Commons validation cache does not match its file name: {path}")
    accepted_values = cast(list[object], accepted)
    if any(not isinstance(item, str) or item not in expected for item in accepted_values):
        raise ValueError(f"Commons validation cache has invalid accepted files: {path}")
    return {item for item in accepted_values if isinstance(item, str)}


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (serialized + "\n").encode()


def _chunked(values: tuple[str, ...], size: int) -> Iterable[tuple[str, ...]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _qid_number(value: str) -> int:
    if len(value) < 2 or value[0] != "Q" or not value[1:].isdigit():
        raise ValueError(f"invalid QID: {value}")
    return int(value[1:])
