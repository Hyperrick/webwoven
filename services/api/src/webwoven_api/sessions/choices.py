"""Deterministic, route-safe projection of a dense graph into playable choices."""

from collections.abc import Mapping
from dataclasses import dataclass

from webwoven_api.graph.contracts import GraphEdge

MAX_VISIBLE_TARGETS = 6


@dataclass(frozen=True, slots=True)
class _TargetChoice:
    target_id: str
    label: str
    relation_key: str
    distance: int | None


def select_visible_edges(
    edges: tuple[GraphEdge, ...],
    distances: Mapping[str, int],
    *,
    current_distance: int | None,
    limit: int = MAX_VISIBLE_TARGETS,
) -> tuple[GraphEdge, ...]:
    """Keep a small, diverse set that always exposes a route toward the goal."""
    if limit < 1:
        raise ValueError("visible edge limit must be positive")

    by_target: dict[str, list[GraphEdge]] = {}
    for edge in edges:
        by_target.setdefault(edge.target_id, []).append(edge)

    choices = [
        _choice(target_edges, distances.get(target_id))
        for target_id, target_edges in by_target.items()
    ]
    relation_positions: dict[tuple[int, str], int] = {}

    def rank(choice: _TargetChoice) -> tuple[int, int, int, str, str]:
        tier = _distance_tier(choice.distance, current_distance)
        relation_key = (tier, choice.relation_key)
        relation_position = relation_positions.get(relation_key, 0)
        relation_positions[relation_key] = relation_position + 1
        distance = choice.distance if choice.distance is not None else 1_000_000
        return tier, relation_position, distance, choice.label.casefold(), choice.target_id

    ordered = sorted(
        sorted(
            choices, key=lambda item: (item.relation_key, item.label.casefold(), item.target_id)
        ),
        key=rank,
    )
    selected_targets = {choice.target_id for choice in ordered[:limit]}
    return tuple(edge for edge in edges if edge.target_id in selected_targets)


def _choice(edges: list[GraphEdge], distance: int | None) -> _TargetChoice:
    primary = min(
        edges,
        key=lambda edge: (edge.relation_key, edge.target.label.casefold(), edge.id),
    )
    return _TargetChoice(
        target_id=primary.target_id,
        label=primary.target.label,
        relation_key=primary.relation_key,
        distance=distance,
    )


def _distance_tier(distance: int | None, current_distance: int | None) -> int:
    if distance is None:
        return 3
    if current_distance is None or distance < current_distance:
        return 0
    if distance == current_distance:
        return 1
    return 2
