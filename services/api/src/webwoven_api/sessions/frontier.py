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
    if _only_choice_forces_a_dead_end(graph, round_, navigation, available_edges):
        return ()
    target_ids = tuple(edge.target_id for edge in available_edges)
    distances = graph.distances_to_target(round_.id, target_ids)
    current_distance = graph.distance_to_target(round_.id, source_id)
    return select_visible_edges(
        available_edges,
        distances,
        current_distance=current_distance,
    )


def _only_choice_forces_a_dead_end(
    graph: GraphReader,
    round_: Round,
    navigation: NavigationState,
    available_edges: tuple[GraphEdge, ...],
) -> bool:
    """Stop before a one-way corridor that cannot reach a goal or a new choice."""
    target_ids = {edge.target_id for edge in available_edges}
    if len(target_ids) != 1:
        return False

    current_id = next(iter(target_ids))
    visited = set(navigation.active_route_ids)
    while True:
        if current_id == round_.target_id:
            return False
        visited.add(current_id)
        next_ids = {
            edge.target_id for edge in graph.get_edges(current_id) if edge.target_id not in visited
        }
        if not next_ids:
            return True
        if len(next_ids) > 1:
            return False
        current_id = next(iter(next_ids))
