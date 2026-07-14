"""Own the route-safe, deterministic frontier for a pinned round state."""

from webwoven_api.domain.navigation import NavigationState
from webwoven_api.graph.contracts import GraphEdge, GraphReader, Round
from webwoven_api.sessions.choices import select_visible_edges


def playable_edges_for(
    graph: GraphReader,
    round_: Round,
    navigation: NavigationState,
) -> tuple[GraphEdge, ...]:
    """Project choices after excluding every entity in the active route."""
    source_id = navigation.current_id
    available_edges = tuple(
        edge
        for edge in graph.get_edges(source_id)
        if edge.target_id not in navigation.active_route_ids
    )
    target_ids = tuple(edge.target_id for edge in available_edges)
    distances = graph.distances_to_target(round_.id, target_ids)
    current_distance = graph.distance_to_target(round_.id, source_id)
    return select_visible_edges(
        available_edges,
        distances,
        current_distance=current_distance,
    )
