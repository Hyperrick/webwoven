from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

from .normalization import normalize_edges, wikidata_relation_profiles
from .registry import RelationRegistry
from .relation_semantics import RelationEntityProfile, semantic_tags_for_profile


class SemanticRefreshError(ValueError):
    """Raised when a recorded source batch cannot be trusted for a semantic rebuild."""


def refresh_wikidata_relationships(
    source: Mapping[str, Any],
    cache_dir: Path,
    registry: RelationRegistry,
    allowed_qids: Iterable[str],
) -> dict[str, Any]:
    """Rebuild edge wording from recorded immutable batches without network access."""
    if source.get("schema_version") != 2 or source.get("source") != "wikidata":
        raise SemanticRefreshError("graph source must be a Wikidata schema-v2 acquisition")
    qids = frozenset(allowed_qids)
    raw_entities = _load_recorded_entities(source.get("source_batches"), cache_dir)
    missing = sorted(qids - raw_entities.keys(), key=_qid_number)
    if missing:
        detail = f"starting with {missing[0]}"
        raise SemanticRefreshError(
            f"recorded source batches are missing {len(missing)} graph entities, {detail}"
        )
    refreshed = dict(source)
    profiles = wikidata_relation_profiles(raw_entities, qids)
    refreshed["entities"] = _refresh_entity_semantics(source.get("entities"), profiles, qids)
    refreshed["edges"] = [
        edge.to_dict() for edge in normalize_edges(raw_entities, registry, allowed_qids=qids)
    ]
    return refreshed


def _refresh_entity_semantics(
    value: Any,
    profiles: Mapping[str, RelationEntityProfile],
    allowed_qids: frozenset[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise SemanticRefreshError("entities must be a list")
    refreshed: list[dict[str, Any]] = []
    for index, item in enumerate(cast(list[Any], value)):
        if not isinstance(item, dict):
            raise SemanticRefreshError(f"entity {index} must be an object")
        entity = dict(cast(dict[str, Any], item))
        qid = entity.get("id")
        if not isinstance(qid, str) or qid not in allowed_qids:
            raise SemanticRefreshError(f"entity {index} has an unexpected ID")
        profile = profiles[qid]
        entity["label"] = profile.label
        entity["description"] = profile.description
        semantic_tags = sorted(semantic_tags_for_profile(profile))
        if semantic_tags:
            entity["semantic_tags"] = semantic_tags
        else:
            entity.pop("semantic_tags", None)
        refreshed.append(entity)
    if len(refreshed) != len(allowed_qids):
        raise SemanticRefreshError("entities do not match the allowed graph IDs")
    return refreshed


def _load_recorded_entities(value: Any, cache_dir: Path) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise SemanticRefreshError("source_batches must be a non-empty list")
    entities: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(cast(list[Any], value)):
        if not isinstance(item, dict):
            raise SemanticRefreshError(f"source batch {index} must be an object")
        batch = cast(dict[str, Any], item)
        path = _batch_path(cache_dir, batch.get("path"), index)
        payload = path.read_bytes()
        expected_hash = batch.get("sha256")
        if (
            not isinstance(expected_hash, str)
            or hashlib.sha256(payload).hexdigest() != expected_hash
        ):
            raise SemanticRefreshError(f"source batch {path.name} failed SHA-256 verification")
        parsed: object = json.loads(payload)
        if not isinstance(parsed, dict):
            raise SemanticRefreshError(f"source batch {path.name} has no entities object")
        parsed_object = cast(dict[str, Any], parsed)
        entity_values = parsed_object.get("entities")
        if not isinstance(entity_values, dict):
            raise SemanticRefreshError(f"source batch {path.name} has no entities object")
        for qid, entity in cast(dict[str, Any], entity_values).items():
            if not _is_qid(qid) or not isinstance(entity, dict):
                continue
            normalized = cast(dict[str, Any], entity)
            existing = entities.get(qid)
            if existing is not None and existing != normalized:
                raise SemanticRefreshError(f"recorded source batches disagree about {qid}")
            entities[qid] = normalized
    return entities


def _batch_path(cache_dir: Path, value: Any, index: int) -> Path:
    if not isinstance(value, str) or not value or Path(value).name != value:
        raise SemanticRefreshError(f"source batch {index} has an unsafe cache path")
    path = cache_dir / value
    if not path.is_file():
        raise SemanticRefreshError(f"recorded source batch is missing: {path}")
    return path


def _is_qid(value: object) -> bool:
    return (
        isinstance(value, str) and value.startswith("Q") and len(value) > 1 and value[1:].isdigit()
    )


def _qid_number(value: str) -> int:
    if not _is_qid(value):
        raise SemanticRefreshError(f"invalid QID: {value}")
    return int(value[1:])
