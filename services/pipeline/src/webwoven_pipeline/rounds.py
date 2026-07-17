from __future__ import annotations

import hashlib
from collections import deque
from collections.abc import Iterable, Mapping

from .models import Edge, Entity, Round
from .taxonomy import CATEGORIES

TIME_WINDOWS = {"easy": 120, "normal": 180, "hard": 240}
CANDIDATE_DISTRIBUTION = {"easy": 4, "normal": 4, "hard": 2}
PUBLISHED_DISTRIBUTION = {"easy": 2, "normal": 1, "hard": 1}
DEFAULT_SELECTION_SEED = "webwoven-build-week-v1"


class RoundCapacityError(ValueError):
    """Raised when a graph cannot satisfy the locked round distribution."""


def generate_rounds(
    entities: Iterable[Entity],
    edges: Iterable[Edge],
    *,
    selection_seed: str = DEFAULT_SELECTION_SEED,
    endpoint_ids: Iterable[str] | None = None,
) -> tuple[Round, ...]:
    """Choose ten stable candidates per category and publish four per category."""
    entity_values = tuple(entities)
    allowed_endpoints = frozenset(endpoint_ids) if endpoint_ids is not None else None
    playable_edges = tuple(edge for edge in edges if edge.playable)
    adjacency = _adjacency(playable_edges)
    labels = {entity.id: entity.label for entity in entity_values}
    selected: list[Round] = []

    for category in CATEGORIES:
        category_ids = sorted(
            entity.id
            for entity in entity_values
            if entity.category == category
            and (allowed_endpoints is None or entity.id in allowed_endpoints)
        )
        buckets = _candidate_buckets(category_ids, adjacency)
        for difficulty in ("easy", "normal", "hard"):
            needed = CANDIDATE_DISTRIBUTION[difficulty]
            ranked = sorted(
                buckets[difficulty],
                key=lambda pair: (
                    _selection_hash(selection_seed, category, difficulty, pair[0], pair[1]),
                    labels[pair[0]],
                    labels[pair[1]],
                    pair,
                ),
            )
            if len(ranked) < needed:
                raise RoundCapacityError(
                    f"{category}/{difficulty} needs {needed} pairs but graph provides {len(ranked)}"
                )
            for index, (start_id, target_id, distance) in enumerate(ranked[:needed]):
                selected.append(
                    Round(
                        id=_round_id(category, difficulty, start_id, target_id),
                        start_id=start_id,
                        target_id=target_id,
                        category=category,
                        difficulty=difficulty,
                        optimal_distance=distance,
                        time_window=TIME_WINDOWS[difficulty],
                        published=index < PUBLISHED_DISTRIBUTION[difficulty],
                    )
                )

    rounds = tuple(sorted(selected, key=lambda item: item.id))
    _assert_distribution(rounds)
    return rounds


def shortest_distances_to_target(
    target_id: str,
    edges: Iterable[Edge],
) -> dict[str, int]:
    reverse: dict[str, set[str]] = {}
    for edge in edges:
        if edge.playable:
            reverse.setdefault(edge.target_id, set()).add(edge.source_id)
    distances = {target_id: 0}
    queue: deque[str] = deque([target_id])
    while queue:
        current = queue.popleft()
        for predecessor in sorted(reverse.get(current, ())):
            if predecessor not in distances:
                distances[predecessor] = distances[current] + 1
                queue.append(predecessor)
    return distances


def _candidate_buckets(
    entity_ids: list[str],
    adjacency: Mapping[str, tuple[str, ...]],
) -> dict[str, list[tuple[str, str, int]]]:
    buckets: dict[str, list[tuple[str, str, int]]] = {
        "easy": [],
        "normal": [],
        "hard": [],
    }
    allowed_targets = frozenset(entity_ids)
    for start_id in entity_ids:
        if len(adjacency.get(start_id, ())) < 2:
            continue
        distances = _forward_distances(start_id, adjacency, maximum=8)
        for target_id, distance in distances.items():
            difficulty = _difficulty(distance)
            if target_id in allowed_targets and difficulty is not None:
                buckets[difficulty].append((start_id, target_id, distance))
    return buckets


def _forward_distances(
    start_id: str,
    adjacency: Mapping[str, tuple[str, ...]],
    *,
    maximum: int,
) -> dict[str, int]:
    distances = {start_id: 0}
    queue: deque[str] = deque([start_id])
    while queue:
        current = queue.popleft()
        if distances[current] >= maximum:
            continue
        for target in adjacency.get(current, ()):
            if target not in distances:
                distances[target] = distances[current] + 1
                queue.append(target)
    distances.pop(start_id)
    return distances


def _adjacency(edges: Iterable[Edge]) -> dict[str, tuple[str, ...]]:
    values: dict[str, set[str]] = {}
    for edge in edges:
        values.setdefault(edge.source_id, set()).add(edge.target_id)
    return {source: tuple(sorted(targets)) for source, targets in values.items()}


def _difficulty(distance: int) -> str | None:
    if distance == 2:
        return "easy"
    if distance == 3:
        return "normal"
    if 4 <= distance <= 8:
        return "hard"
    return None


def _selection_hash(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


def _round_id(category: str, difficulty: str, start_id: str, target_id: str) -> str:
    digest = _selection_hash("round-v1", category, difficulty, start_id, target_id)[:16]
    return f"round-{digest}"


def _assert_distribution(rounds: tuple[Round, ...]) -> None:
    if len(rounds) != 100 or sum(item.published for item in rounds) != 40:
        raise AssertionError("round generator violated the 100 candidate / 40 published contract")
    for category in CATEGORIES:
        category_rounds = tuple(item for item in rounds if item.category == category)
        if len(category_rounds) != 10 or sum(item.published for item in category_rounds) != 4:
            raise AssertionError(f"round generator violated the category contract for {category}")
