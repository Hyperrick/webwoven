"""Playable frontiers own active-route exclusion before choice ranking."""

from webwoven_api.domain.navigation import NavigationState, follow_edge, start_navigation
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.sessions.choices import MAX_VISIBLE_TARGETS
from webwoven_api.sessions.frontier import playable_edges_for


def test_frontier_excludes_every_target_in_the_active_route() -> None:
    graph = MemoryGraphReader.demo()
    round_ = graph.rounds[0]
    navigation = follow_edge(
        start_navigation("Q1"),
        edge_source_id="Q1",
        edge_target_id="Q2",
    )

    visible = playable_edges_for(graph, round_, navigation)

    assert {edge.target_id for edge in visible} == {"Q3"}


def test_frontier_can_be_empty_when_every_target_is_in_the_active_route() -> None:
    graph = MemoryGraphReader.demo()
    round_ = graph.rounds[0]
    navigation = NavigationState(
        stack=("Q1", "Q3", "Q2"),
        trail=("Q1", "Q3", "Q2"),
        moves=2,
    )

    visible = playable_edges_for(graph, round_, navigation)

    assert visible == ()


def test_dense_frontier_refills_after_active_route_targets_are_removed() -> None:
    graph, round_ = _dense_graph()
    navigation = follow_edge(
        start_navigation("Q1"),
        edge_source_id="Q1",
        edge_target_id="Q2",
    )

    visible = playable_edges_for(graph, round_, navigation)

    assert len({edge.target_id for edge in visible}) == MAX_VISIBLE_TARGETS
    assert "Q1" not in {edge.target_id for edge in visible}


def _dense_graph() -> tuple[MemoryGraphReader, Round]:
    entities = {
        f"Q{index}": Entity(
            id=f"Q{index}",
            label=f"Entity {index:02d}",
            description=None,
            entity_type="item",
            category="science",
        )
        for index in range(1, 10)
    }
    edges = tuple(
        GraphEdge(
            id=f"edge-{target_id}",
            source_id="Q2",
            target_id=target_id,
            relation_key="P361",
            relation_label="part of",
            statement_id=f"statement-{target_id}",
            explanation=f"Entity 02 connects to {entities[target_id].label}.",
            target=entities[target_id],
        )
        for target_id in ("Q1", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9")
    )
    round_ = Round(
        id="dense-round",
        start_id="Q1",
        target_id="Q9",
        category="science",
        difficulty=Difficulty.NORMAL,
        optimal_distance=3,
        time_window=180,
        published=True,
    )
    distances = {(round_.id, "Q2"): 3, (round_.id, "Q1"): 1}
    distances.update(
        {(round_.id, target_id): 2 for target_id in ("Q3", "Q4", "Q5", "Q6", "Q7", "Q8")}
    )
    distances[(round_.id, "Q9")] = 0
    return MemoryGraphReader(entities, edges, (round_,), distances), round_
