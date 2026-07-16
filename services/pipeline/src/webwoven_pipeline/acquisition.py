from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol, cast

from .registry import RelationRegistry
from .seeds import SeedCatalog
from .statement_policy import eligible_statements
from .taxonomy import CATEGORIES, category_sort_key
from .wikidata import WikidataBatch, entities_from_batches


@dataclass(frozen=True, slots=True)
class AcquisitionResult:
    entities: dict[str, dict[str, Any]]
    category_by_qid: dict[str, str]
    batches: tuple[WikidataBatch, ...]


class EntityBatchClient(Protocol):
    def fetch_entities(self, qids: Iterable[str]) -> tuple[WikidataBatch, ...]: ...


def acquire_graph(
    seeds: SeedCatalog,
    registry: RelationRegistry,
    client: EntityBatchClient,
    *,
    hops: int = 2,
    max_entities: int = 10_000,
) -> AcquisitionResult:
    """Expand curated anchors through configured outgoing statements."""
    if hops < 0:
        raise ValueError("hops cannot be negative")
    if max_entities < len(seeds.seeds):
        raise ValueError("max_entities cannot be smaller than the seed catalog")

    categories = seeds.category_by_qid
    raw_entities: dict[str, dict[str, Any]] = {}
    batches: list[WikidataBatch] = []
    frontier = set(seeds.qids)

    for depth in range(hops + 1):
        pending = tuple(sorted(frontier - raw_entities.keys(), key=_qid_number))
        if not pending:
            break
        fetched = client.fetch_entities(pending)
        batches.extend(fetched)
        raw_entities.update(entities_from_batches(fetched))
        if depth == hops:
            break

        discovered_categories: dict[str, list[str]] = {}
        for source_qid in pending:
            source = raw_entities.get(source_qid)
            if source is None:
                continue
            source_category = categories[source_qid]
            for target_qid in _outgoing_targets(source, registry):
                discovered_categories.setdefault(target_qid, []).append(source_category)

        available = max_entities - len(raw_entities)
        unseen_categories = {
            target_qid: source_categories
            for target_qid, source_categories in discovered_categories.items()
            if target_qid not in raw_entities
        }
        selected_categories = _balanced_frontier(unseen_categories, available)
        selected = tuple(selected_categories)
        categories.update(selected_categories)
        frontier = set(selected)

    ordered_entities = dict(sorted(raw_entities.items(), key=lambda item: _qid_number(item[0])))
    ordered_categories = {qid: categories[qid] for qid in ordered_entities if qid in categories}
    return AcquisitionResult(ordered_entities, ordered_categories, tuple(batches))


def _balanced_frontier(
    discovered_categories: dict[str, list[str]],
    limit: int,
) -> dict[str, str]:
    """Choose a deterministic, category-balanced set of previously unseen targets."""
    categorized = {
        qid: min(source_categories, key=category_sort_key)
        for qid, source_categories in discovered_categories.items()
    }
    by_category = {
        category: sorted(
            (qid for qid, assigned in categorized.items() if assigned == category),
            key=_qid_number,
        )
        for category in CATEGORIES
    }
    selected: dict[str, str] = {}
    offsets = {category: 0 for category in CATEGORIES}
    while len(selected) < limit:
        added = False
        for category in CATEGORIES:
            offset = offsets[category]
            values = by_category[category]
            if offset >= len(values):
                continue
            qid = values[offset]
            offsets[category] += 1
            selected[qid] = category
            added = True
            if len(selected) == limit:
                break
        if not added:
            break
    return selected


def _outgoing_targets(entity: dict[str, Any], registry: RelationRegistry) -> tuple[str, ...]:
    claims_value = entity.get("claims")
    if not isinstance(claims_value, dict):
        return ()
    claims = cast(dict[str, Any], claims_value)
    targets: list[str] = []
    for relation in registry.relations:
        statements_value = claims.get(relation.key)
        if not isinstance(statements_value, list):
            continue
        statements = cast(list[Any], statements_value)
        relation_targets: set[str] = set()
        for statement in eligible_statements(statements):
            target = _statement_target(statement)
            if target is not None and target != entity.get("id"):
                relation_targets.add(target)
        targets.extend(sorted(relation_targets, key=_qid_number)[: relation.max_targets])
    return tuple(dict.fromkeys(targets))


def _statement_target(value: Any) -> str | None:
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
    target = target_value.get("id")
    valid = isinstance(target, str) and target.startswith("Q") and target[1:].isdigit()
    return cast(str, target) if valid else None


def _qid_number(value: str) -> int:
    return int(value[1:])
