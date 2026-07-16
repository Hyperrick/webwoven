"""Build route-aware hint candidates for the current playable frontier."""

from collections import deque
from collections.abc import Iterable

from webwoven_api.domain.hints import HintCandidate
from webwoven_api.graph.contracts import GraphEdge, GraphReader, Round


def route_aware_hint_candidates(
    graph: GraphReader,
    round_: Round,
    edges: Iterable[GraphEdge],
    *,
    blocked_entity_ids: frozenset[str],
) -> tuple[HintCandidate, ...]:
    return tuple(
        HintCandidate(
            relation_key=edge.relation_key,
            entity_id=edge.target_id,
            entity_label=edge.target.label,
            distance=_route_distance(
                graph,
                round_,
                edge.target_id,
                blocked_entity_ids=blocked_entity_ids,
            ),
        )
        for edge in edges
    )


def _route_distance(
    graph: GraphReader,
    round_: Round,
    start_id: str,
    *,
    blocked_entity_ids: frozenset[str],
) -> int | None:
    if start_id == round_.target_id:
        return 0
    if graph.distance_to_target(round_.id, start_id) is None:
        return None

    visited = set(blocked_entity_ids)
    visited.add(start_id)
    queue = deque([(start_id, 0)])
    while queue:
        source_id, distance = queue.popleft()
        edges = tuple(edge for edge in graph.get_edges(source_id) if edge.target_id not in visited)
        grounded = graph.distances_to_target(
            round_.id,
            tuple(edge.target_id for edge in edges),
        )
        for edge in sorted(edges, key=lambda candidate: candidate.id):
            target_id = edge.target_id
            if target_id == round_.target_id:
                return distance + 1
            if target_id not in grounded:
                continue
            visited.add(target_id)
            queue.append((target_id, distance + 1))
    return None
