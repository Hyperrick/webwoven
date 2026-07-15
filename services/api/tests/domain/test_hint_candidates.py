"""Route-aware hint candidate projection tests."""

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.sessions.hint_candidates import route_aware_hint_candidates


def test_hint_candidates_do_not_route_back_through_the_active_path() -> None:
    entities = {
        qid: Entity(qid, label, None, "work", "arts_culture")
        for qid, label in {
            "Q1": "Artist",
            "Q2": "Dead-end work",
            "Q3": "Promising work",
            "Q4": "Goal",
        }.items()
    }
    edges = (
        _edge("edge-dead", "Q1", "Q2", entities, "P800"),
        _edge("edge-good", "Q1", "Q3", entities, "P800"),
        _edge("edge-back", "Q2", "Q1", entities, "P170"),
        _edge("edge-goal", "Q3", "Q4", entities, "P361"),
    )
    round_ = Round(
        "round",
        "Q1",
        "Q4",
        "arts_culture",
        Difficulty.HARD,
        2,
        240,
        True,
    )
    graph = MemoryGraphReader(
        entities,
        edges,
        (round_,),
        {
            ("round", "Q1"): 2,
            ("round", "Q2"): 3,
            ("round", "Q3"): 1,
            ("round", "Q4"): 0,
        },
    )

    candidates = route_aware_hint_candidates(
        graph,
        round_,
        edges[:2],
        blocked_entity_ids=frozenset({"Q1"}),
    )

    assert {candidate.entity_id: candidate.distance for candidate in candidates} == {
        "Q2": None,
        "Q3": 1,
    }


def _edge(
    edge_id: str,
    source: str,
    target: str,
    entities: dict[str, Entity],
    relation_key: str,
) -> GraphEdge:
    return GraphEdge(
        edge_id,
        source,
        target,
        relation_key,
        "related to",
        f"statement-{edge_id}",
        f"{source} relates to {target}.",
        entities[target],
    )
