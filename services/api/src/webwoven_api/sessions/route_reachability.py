"""Own route-aware target search for a pinned graph and active route."""

from dataclasses import dataclass
from heapq import heappop, heappush

from webwoven_api.graph.contracts import GraphReader, Round


@dataclass(frozen=True, slots=True)
class RouteReachability:
    """Shortest route-safe distance and its first move from one entity."""

    distance: int
    next_target_id: str | None


def route_reachability_to_target(
    graph: GraphReader,
    round_: Round,
    start_id: str,
    *,
    blocked_entity_ids: frozenset[str],
) -> RouteReachability | None:
    """Find one deterministic shortest path without revisiting blocked entities."""
    if start_id == round_.target_id:
        return RouteReachability(distance=0, next_target_id=None)
    global_distance = graph.distance_to_target(round_.id, start_id)
    if global_distance is None:
        return None

    visited = set(blocked_entity_ids)
    visited.discard(start_id)
    queue: list[tuple[int, int, str, str, str | None]] = [(global_distance, 0, "", start_id, None)]
    while queue:
        _, distance, _, source_id, first_target_id = heappop(queue)
        if source_id in visited:
            continue
        visited.add(source_id)
        edges = tuple(edge for edge in graph.get_edges(source_id) if edge.target_id not in visited)
        grounded = graph.distances_to_target(
            round_.id,
            tuple(edge.target_id for edge in edges),
        )
        for edge in sorted(edges, key=lambda candidate: candidate.id):
            target_id = edge.target_id
            next_target_id = first_target_id or target_id
            if target_id == round_.target_id:
                return RouteReachability(
                    distance=distance + 1,
                    next_target_id=next_target_id,
                )
            target_distance = grounded.get(target_id)
            if target_distance is None:
                continue
            next_distance = distance + 1
            heappush(
                queue,
                (
                    next_distance + target_distance,
                    next_distance,
                    next_target_id,
                    target_id,
                    next_target_id,
                ),
            )
    return None


def route_distance_to_target(
    graph: GraphReader,
    round_: Round,
    start_id: str,
    *,
    blocked_entity_ids: frozenset[str],
) -> int | None:
    """Return the shortest route-safe distance for hint projection."""
    reachability = route_reachability_to_target(
        graph,
        round_,
        start_id,
        blocked_entity_ids=blocked_entity_ids,
    )
    return reachability.distance if reachability is not None else None
