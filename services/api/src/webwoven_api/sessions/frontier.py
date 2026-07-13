"""Resolve the deterministic playable frontier for a pinned round state."""

from webwoven_api.graph.contracts import GraphEdge, GraphReader, Round
from webwoven_api.sessions.choices import select_visible_edges


def visible_edges_for(
    graph: GraphReader,
    round_: Round,
    source_id: str,
) -> tuple[GraphEdge, ...]:
    available_edges = graph.get_edges(source_id)
    target_ids = tuple(edge.target_id for edge in available_edges)
    distances = graph.distances_to_target(round_.id, target_ids)
    current_distance = graph.distance_to_target(round_.id, source_id)
    return select_visible_edges(
        available_edges,
        distances,
        current_distance=current_distance,
    )
