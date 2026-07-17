"""Deterministic eligibility policy for automatically assigned rounds."""

from collections.abc import Iterable

from webwoven_api.graph.contracts import GraphReader, Round


def has_multiple_opening_routes(graph: GraphReader, round_: Round) -> bool:
    """Return whether the playable start edges reach multiple entities."""
    opening_targets = {
        edge.target_id
        for edge in graph.get_edges(round_.start_id)
        if edge.target_id != round_.start_id
    }
    return len(opening_targets) > 1


def eligible_rounds(graph: GraphReader, rounds: Iterable[Round]) -> tuple[Round, ...]:
    """Keep automatic round pools deterministic and free of forced openings."""
    return tuple(round_ for round_ in rounds if has_multiple_opening_routes(graph, round_))
