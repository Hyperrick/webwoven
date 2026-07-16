from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable
from typing import Any

from .models import Edge, Entity, Round
from .rounds import (
    CANDIDATE_DISTRIBUTION,
    PUBLISHED_DISTRIBUTION,
    TIME_WINDOWS,
    shortest_distances_to_target,
)
from .taxonomy import CATEGORIES


class RoundValidationError(ValueError):
    """Raised when generated rounds do not satisfy the publication policy."""


def validate_round_selection(
    rounds: Iterable[Round],
    entities: Iterable[Entity],
    edges: Iterable[Edge],
    *,
    endpoint_ids: Iterable[str],
    playable_relation_keys: Iterable[str],
    source_kind: str,
    selection_seed: str,
    registry_version: int,
) -> dict[str, Any]:
    """Validate the deterministic 40-round publication set and return its audit report."""
    round_values = tuple(sorted(rounds, key=lambda item: item.id))
    entity_values = tuple(entities)
    edge_values = tuple(edges)
    allowed_endpoints = frozenset(endpoint_ids)
    allowed_relations = frozenset(playable_relation_keys)
    labels = {item.id: item.label.strip() for item in entity_values}
    categories = {item.id: item.category for item in entity_values}
    published = tuple(item for item in round_values if item.published)

    per_round = tuple(
        _round_result(item, edge_values, allowed_endpoints, labels, categories)
        for item in round_values
    )
    candidate_distribution = Counter((item.category, item.difficulty) for item in round_values)
    published_distribution = Counter((item.category, item.difficulty) for item in published)

    checks = {
        "candidate_count": len(round_values) == 100,
        "published_count": len(published) == 40,
        "unique_round_ids": len({item.id for item in round_values}) == len(round_values),
        "candidate_distribution": candidate_distribution
        == _expected_distribution(CANDIDATE_DISTRIBUTION),
        "published_distribution": published_distribution
        == _expected_distribution(PUBLISHED_DISTRIBUTION),
        "unique_candidate_pairs": len({(item.start_id, item.target_id) for item in round_values})
        == len(round_values),
        "all_round_checks": all(result["passed"] for result in per_round),
        "allowlisted_playable_relations": all(
            not edge.playable or edge.relation_key in allowed_relations for edge in edge_values
        ),
        "playable_edge_metadata_present": all(
            not edge.playable
            or (bool(edge.statement_id.strip()) and bool(edge.explanation.strip()))
            for edge in edge_values
        ),
    }
    failed = tuple(check_id for check_id, passed in checks.items() if not passed)
    if failed:
        raise RoundValidationError(f"round publication validation failed: {', '.join(failed)}")

    return {
        "version": 1,
        "policy": "deterministic-round-publication-v1",
        "source_kind": source_kind,
        "status": "passed",
        "inputs": {
            "selection_seed": selection_seed,
            "endpoint_catalog_sha256": _endpoint_catalog_hash(allowed_endpoints),
            "registry_version": registry_version,
        },
        "summary": {
            "candidate_rounds": len(round_values),
            "published_rounds": len(published),
            "curated_endpoints": len(allowed_endpoints),
        },
        "checks": checks,
        "rounds": list(per_round),
    }


def _round_result(
    item: Round,
    edges: tuple[Edge, ...],
    allowed_endpoints: frozenset[str],
    labels: dict[str, str],
    categories: dict[str, str],
) -> dict[str, Any]:
    actual_distance = shortest_distances_to_target(item.target_id, edges).get(item.start_id)
    checks = {
        "distinct_endpoints": item.start_id != item.target_id,
        "curated_endpoints": item.start_id in allowed_endpoints
        and item.target_id in allowed_endpoints,
        "labeled_endpoints": bool(labels.get(item.start_id)) and bool(labels.get(item.target_id)),
        "category_endpoints": categories.get(item.start_id) == item.category
        and categories.get(item.target_id) == item.category,
        "shortest_distance": actual_distance == item.optimal_distance,
        "difficulty_band": _difficulty_matches(item.difficulty, actual_distance),
        "time_window": TIME_WINDOWS.get(item.difficulty) == item.time_window,
    }
    return {
        "round_id": item.id,
        "publication_status": "published" if item.published else "reserve",
        "passed": all(checks.values()),
        "checks": checks,
    }


def _endpoint_catalog_hash(endpoint_ids: frozenset[str]) -> str:
    return hashlib.sha256("\0".join(sorted(endpoint_ids)).encode()).hexdigest()


def _difficulty_matches(difficulty: str, distance: int | None) -> bool:
    if difficulty == "easy":
        return distance == 2
    if difficulty == "normal":
        return distance == 3
    if difficulty == "hard":
        return distance is not None and 4 <= distance <= 8
    return False


def _expected_distribution(per_category: dict[str, int]) -> Counter[tuple[str, str]]:
    return Counter(
        {
            (category, difficulty): count
            for category in CATEGORIES
            for difficulty, count in per_category.items()
        }
    )
