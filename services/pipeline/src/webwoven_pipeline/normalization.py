from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from typing import Any, cast

from .models import Edge, Entity, MediaRecord
from .registry import Relation, RelationRegistry
from .relation_sentences import format_relation_sentence
from .statement_policy import eligible_statements


def normalize_entities(
    raw_entities: Mapping[str, dict[str, Any]],
    category_by_qid: Mapping[str, str],
    *,
    media_records: Mapping[str, MediaRecord] | None = None,
    media_paths: Mapping[str, str] | None = None,
) -> tuple[Entity, ...]:
    media_records = media_records or {}
    media_paths = media_paths or {}
    entities: list[Entity] = []
    for qid, raw in sorted(raw_entities.items(), key=lambda item: _qid_number(item[0])):
        if raw.get("missing") is True or qid not in category_by_qid:
            continue
        label = _language_value(raw, "labels")
        if not label:
            continue
        image_name = _commons_file_name(raw)
        media = media_records.get(image_name) if image_name else None
        entities.append(
            Entity(
                id=qid,
                label=label,
                description=_language_value(raw, "descriptions"),
                entity_type="wikidata_item",
                category=category_by_qid[qid],
                image_path=media_paths.get(image_name) if image_name and media else None,
                image_attribution=media.to_dict() if media else None,
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
    labels = {qid: _language_value(raw_entities[qid], "labels") for qid in known_qids}
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
            for target_id, statement_id in targets:
                if target_id == source_id:
                    continue
                forward = _make_edge(
                    source_id,
                    target_id,
                    labels[source_id],
                    labels[target_id],
                    relation,
                    statement_id,
                    inverse=False,
                )
                edges.setdefault((source_id, target_id, relation.key), forward)
                if relation.inverse_label:
                    inverse = _make_edge(
                        source_id,
                        target_id,
                        labels[source_id],
                        labels[target_id],
                        relation,
                        statement_id,
                        inverse=True,
                    )
                    edges.setdefault((target_id, source_id, relation.key), inverse)
    return tuple(sorted(edges.values(), key=lambda edge: edge.id))


def _valid_targets(
    statements: list[Any],
    limit: int,
    known_qids: frozenset[str],
) -> tuple[tuple[str, str], ...]:
    values: dict[str, str] = {}
    for statement in eligible_statements(statements):
        parsed = _statement_target(statement)
        if parsed is not None and parsed[0] in known_qids:
            target_id, statement_id = parsed
            values.setdefault(target_id, statement_id)
    return tuple(sorted(values.items(), key=lambda item: _qid_number(item[0]))[:limit])


def _statement_target(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        return None
    statement = cast(dict[str, Any], value)
    if statement.get("rank") == "deprecated":
        return None
    mainsnak_value = statement.get("mainsnak")
    if not isinstance(mainsnak_value, dict):
        return None
    mainsnak = cast(dict[str, Any], mainsnak_value)
    if mainsnak.get("snaktype") != "value":
        return None
    data_value_value = mainsnak.get("datavalue")
    if not isinstance(data_value_value, dict):
        return None
    data_value = cast(dict[str, Any], data_value_value)
    target_value_value = data_value.get("value")
    if not isinstance(target_value_value, dict):
        return None
    target_value = cast(dict[str, Any], target_value_value)
    target_id_value = target_value.get("id")
    valid_qid = (
        isinstance(target_id_value, str)
        and target_id_value.startswith("Q")
        and target_id_value[1:].isdigit()
    )
    if not valid_qid:
        return None
    target_id = cast(str, target_id_value)
    statement_id_value = statement.get("id")
    statement_id = (
        statement_id_value
        if isinstance(statement_id_value, str) and statement_id_value
        else _digest("statement", target_id)
    )
    return target_id, statement_id


def _make_edge(
    source_id: str,
    target_id: str,
    source_label: str,
    target_label: str,
    relation: Relation,
    statement_id: str,
    *,
    inverse: bool,
) -> Edge:
    if inverse:
        edge_source, edge_target = target_id, source_id
        edge_source_label, edge_target_label = target_label, source_label
        direction = "inverse"
    else:
        edge_source, edge_target = source_id, target_id
        edge_source_label, edge_target_label = source_label, target_label
        direction = "forward"
    return Edge(
        id=_digest(edge_source, relation.key, edge_target, direction),
        source_id=edge_source,
        target_id=edge_target,
        relation_key=relation.key,
        statement_id=statement_id,
        explanation=format_relation_sentence(
            relation.key,
            edge_source_label,
            edge_target_label,
            inverse=inverse,
        ),
        inverse=inverse,
        playable=relation.playable,
    )


def _commons_file_name(raw: Mapping[str, Any]) -> str | None:
    claims_value = raw.get("claims")
    if not isinstance(claims_value, dict):
        return None
    claims = cast(dict[str, Any], claims_value)
    statements_value = claims.get("P18")
    if not isinstance(statements_value, list):
        return None
    statements = cast(list[Any], statements_value)
    names: list[str] = []
    for statement in statements:
        if not isinstance(statement, dict):
            continue
        statement_object = cast(dict[str, Any], statement)
        if statement_object.get("rank") == "deprecated":
            continue
        mainsnak_value = statement_object.get("mainsnak")
        mainsnak = cast(dict[str, Any], mainsnak_value) if isinstance(mainsnak_value, dict) else {}
        data_value_value = mainsnak.get("datavalue")
        data_value = (
            cast(dict[str, Any], data_value_value) if isinstance(data_value_value, dict) else {}
        )
        name = data_value.get("value")
        if isinstance(name, str) and name.strip():
            names.append(name.strip().replace("_", " "))
    return min(names) if names else None


def _language_value(raw: Mapping[str, Any], field: str) -> str:
    values_value = raw.get(field)
    values = cast(dict[str, Any], values_value) if isinstance(values_value, dict) else {}
    english_value = values.get("en")
    english = cast(dict[str, Any], english_value) if isinstance(english_value, dict) else {}
    value = english.get("value")
    return value.strip() if isinstance(value, str) else ""


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:24]


def _qid_number(value: str) -> int:
    return int(value[1:])
