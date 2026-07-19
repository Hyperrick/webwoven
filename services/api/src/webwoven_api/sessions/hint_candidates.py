"""Build route-aware hint candidates for the current playable frontier."""

from collections.abc import Iterable

from webwoven_api.domain.hints import HintCandidate
from webwoven_api.graph.contracts import GraphEdge, GraphReader, Round
from webwoven_api.sessions.route_reachability import route_distance_to_target


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
            distance=route_distance_to_target(
                graph,
                round_,
                edge.target_id,
                blocked_entity_ids=blocked_entity_ids,
            ),
        )
        for edge in edges
    )
