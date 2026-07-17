from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from typing import Any, cast

from .media_candidates import wikidata_media_candidate
from .models import Edge, Entity, MediaRecord
from .registry import Relation, RelationRegistry
from .relation_semantics import (
    SEMANTIC_TAG_RECOGNITION,
    RelationEntityProfile,
    semantic_tags_for_profile,
)
from .relation_sentences import format_relation_sentence
from .statement_policy import eligible_statements

_CLASSIFICATION_PROPERTIES = ("P31", "P279")
_SERIES_ORDINAL_PROPERTY = "P1545"


@dataclass(frozen=True, slots=True)
class _StatementTarget:
    target_id: str
    statement_id: str
    series_ordinal: str | None


def normalize_entities(
    raw_entities: Mapping[str, dict[str, Any]],
    category_by_qid: Mapping[str, str],
    *,
    media_records: Mapping[str, MediaRecord] | None = None,
    media_paths: Mapping[str, str] | None = None,
) -> tuple[Entity, ...]:
    media_records = media_records or {}
    media_paths = media_paths or {}
    known_qids = frozenset(
        qid
        for qid, raw in raw_entities.items()
        if raw.get("missing") is not True
        and qid in category_by_qid
        and _language_value(raw, "labels")
    )
    profiles = wikidata_relation_profiles(raw_entities, known_qids)
    entities: list[Entity] = []
    for qid, raw in sorted(raw_entities.items(), key=lambda item: _qid_number(item[0])):
        if raw.get("missing") is True or qid not in category_by_qid:
            continue
        label = _language_value(raw, "labels")
        if not label:
            continue
        image_name = commons_file_name(raw)
        media = media_records.get(image_name) if image_name else None
        relation_profile = profiles[qid]
        entities.append(
            Entity(
                id=qid,
                label=label,
                description=_language_value(raw, "descriptions"),
                entity_type="wikidata_item",
                category=category_by_qid[qid],
                image_path=media_paths.get(image_name) if image_name and media else None,
                image_attribution=media.to_dict() if media else None,
                semantic_tags=tuple(sorted(semantic_tags_for_profile(relation_profile))),
            )
        )
    return tuple(entities)


def normalize_edges(
    raw_entities: Mapping[str, dict[str, Any]],
    registry: RelationRegistry,
    *,
    allowed_qids: Iterable[str] | None = None,
) -> tuple[Edge, ...]:
    known_qids = (
        frozenset(allowed_qids)
        if allowed_qids is not None
        else frozenset(
            qid
            for qid, raw in raw_entities.items()
            if raw.get("missing") is not True and _language_value(raw, "labels")
        )
    )
    profiles = wikidata_relation_profiles(raw_entities, known_qids)
    edges: dict[tuple[str, str, str], Edge] = {}
    for source_id, raw in sorted(raw_entities.items(), key=lambda item: _qid_number(item[0])):
        if source_id not in known_qids:
            continue
        claims_value = raw.get("claims")
        if not isinstance(claims_value, dict):
            continue
        claims = cast(dict[str, Any], claims_value)
        for relation in registry.relations:
            statements_value = claims.get(relation.key)
            if not isinstance(statements_value, list):
                continue
            statements = cast(list[Any], statements_value)
            targets = _valid_targets(statements, relation.max_targets, known_qids)
            for target in targets:
                target_id = target.target_id
                if target_id == source_id:
                    continue
                forward = _make_edge(
                    source_id,
                    target_id,
                    profiles[source_id],
                    profiles[target_id],
                    relation,
                    target.statement_id,
                    target.series_ordinal,
                    inverse=False,
                )
                edges.setdefault((source_id, target_id, relation.key), forward)
                if relation.inverse_label:
                    inverse = _make_edge(
                        source_id,
                        target_id,
                        profiles[source_id],
                        profiles[target_id],
                        relation,
                        target.statement_id,
                        target.series_ordinal,
                        inverse=True,
                    )
                    edges.setdefault((target_id, source_id, relation.key), inverse)
    return tuple(sorted(edges.values(), key=lambda edge: edge.id))


def _valid_targets(
    statements: list[Any],
    limit: int,
    known_qids: frozenset[str],
) -> tuple[_StatementTarget, ...]:
    values: dict[str, _StatementTarget] = {}
    for statement in eligible_statements(statements):
        parsed = _statement_target(statement)
        if parsed is not None and parsed.target_id in known_qids:
            values.setdefault(parsed.target_id, parsed)
    return tuple(sorted(values.values(), key=lambda item: _qid_number(item.target_id))[:limit])


def _statement_target(value: Any) -> _StatementTarget | None:
    if not isinstance(value, dict):
        return None
    statement = cast(dict[str, Any], value)
    if statement.get("rank") == "deprecated":
        return None
    target_id = _snak_entity_id(statement.get("mainsnak"))
    if target_id is None:
        return None
    statement_id_value = statement.get("id")
    statement_id = (
        statement_id_value
        if isinstance(statement_id_value, str) and statement_id_value
        else _digest("statement", target_id)
    )
    return _StatementTarget(
        target_id=target_id,
        statement_id=statement_id,
        series_ordinal=_series_ordinal(statement),
    )


def _make_edge(
    source_id: str,
    target_id: str,
    source_profile: RelationEntityProfile,
    target_profile: RelationEntityProfile,
    relation: Relation,
    statement_id: str,
    series_ordinal: str | None,
    *,
    inverse: bool,
) -> Edge:
    if inverse:
        edge_source, edge_target = target_id, source_id
        edge_source_profile, edge_target_profile = target_profile, source_profile
        direction = "inverse"
    else:
        edge_source, edge_target = source_id, target_id
        edge_source_profile, edge_target_profile = source_profile, target_profile
        direction = "forward"
    return Edge(
        id=_digest(edge_source, relation.key, edge_target, direction),
        source_id=edge_source,
        target_id=edge_target,
        relation_key=relation.key,
        statement_id=statement_id,
        explanation=format_relation_sentence(
            relation.key,
            edge_source_profile,
            edge_target_profile,
            inverse=inverse,
            series_ordinal=series_ordinal,
        ),
        inverse=inverse,
        playable=relation.playable,
        series_ordinal=series_ordinal,
    )


def wikidata_relation_profile(raw: Mapping[str, Any]) -> RelationEntityProfile:
    """Build the provider-specific evidence used by the source-neutral formatter."""
    claims_value = raw.get("claims")
    claims = cast(dict[str, Any], claims_value) if isinstance(claims_value, dict) else {}
    classification_ids: set[str] = set()
    for property_id in _CLASSIFICATION_PROPERTIES:
        statements_value = claims.get(property_id)
        if not isinstance(statements_value, list):
            continue
        for statement in eligible_statements(cast(list[Any], statements_value)):
            target_id = _snak_entity_id(statement.get("mainsnak"))
            if target_id is not None:
                classification_ids.add(target_id)
    return RelationEntityProfile(
        label=_language_value(raw, "labels"),
        description=_language_value(raw, "descriptions"),
        classification_ids=frozenset(classification_ids),
    )


def wikidata_relation_profiles(
    raw_entities: Mapping[str, dict[str, Any]],
    allowed_qids: Iterable[str],
) -> dict[str, RelationEntityProfile]:
    """Translate provider classifications and relation context into semantic profiles."""
    known_qids = frozenset(allowed_qids)
    profiles = {qid: wikidata_relation_profile(raw_entities[qid]) for qid in known_qids}
    for source_id in known_qids:
        claims_value = raw_entities[source_id].get("claims")
        if not isinstance(claims_value, dict):
            continue
        statements_value = cast(dict[str, Any], claims_value).get("P166")
        if not isinstance(statements_value, list):
            continue
        for statement in eligible_statements(cast(list[Any], statements_value)):
            target_id = _snak_entity_id(statement.get("mainsnak"))
            if target_id not in profiles:
                continue
            profile = profiles[target_id]
            profiles[target_id] = replace(
                profile,
                semantic_tags=profile.semantic_tags | frozenset({SEMANTIC_TAG_RECOGNITION}),
            )
    return profiles


def _snak_entity_id(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    snak = cast(dict[str, Any], value)
    if snak.get("snaktype") != "value":
        return None
    data_value_value = snak.get("datavalue")
    if not isinstance(data_value_value, dict):
        return None
    target_value_value = cast(dict[str, Any], data_value_value).get("value")
    if not isinstance(target_value_value, dict):
        return None
    target_id_value = cast(dict[str, Any], target_value_value).get("id")
    if (
        isinstance(target_id_value, str)
        and target_id_value.startswith("Q")
        and target_id_value[1:].isdigit()
    ):
        return target_id_value
    return None


def _series_ordinal(statement: Mapping[str, Any]) -> str | None:
    qualifiers_value = statement.get("qualifiers")
    if not isinstance(qualifiers_value, dict):
        return None
    values = cast(dict[str, Any], qualifiers_value).get(_SERIES_ORDINAL_PROPERTY)
    if not isinstance(values, list):
        return None
    for value in cast(list[Any], values):
        if not isinstance(value, dict):
            continue
        data_value_value = cast(dict[str, Any], value).get("datavalue")
        if not isinstance(data_value_value, dict):
            continue
        ordinal = cast(dict[str, Any], data_value_value).get("value")
        if isinstance(ordinal, str) and ordinal.strip():
            return ordinal.strip()
    return None


def commons_file_name(raw: Mapping[str, Any]) -> str | None:
    """Return the deterministic preferred entity-specific Commons file name."""
    candidate = wikidata_media_candidate(raw)
    return candidate.file_name if candidate is not None else None


def _language_value(raw: Mapping[str, Any], field: str) -> str:
    values_value = raw.get(field)
    values = cast(dict[str, Any], values_value) if isinstance(values_value, dict) else {}
    english_value = values.get("en")
    english = cast(dict[str, Any], english_value) if isinstance(english_value, dict) else {}
    value = english.get("value")
    if not isinstance(value, str):
        return ""
    visible = "".join(character for character in value if unicodedata.category(character) != "Cf")
    return " ".join(visible.split())


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:24]


def _qid_number(value: str) -> int:
    return int(value[1:])
