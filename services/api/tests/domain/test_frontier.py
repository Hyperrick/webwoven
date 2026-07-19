"""Playable frontiers own active-route exclusion before choice ranking."""

from collections import deque

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


def test_frontier_stops_before_a_forced_dead_end_corridor() -> None:
    graph, round_ = _graph(
        (
            ("Q1", "Q2"),
            ("Q2", "Q1"),
            ("Q2", "Q3"),
            ("Q3", "Q2"),
            ("Q3", "Q4"),
            ("Q4", "Q3"),
            ("Q4", "Q5"),
            ("Q5", "Q4"),
        ),
        target_id="Q9",
    )
    navigation = NavigationState(
        stack=("Q1", "Q2"),
        trail=("Q1", "Q2"),
        moves=1,
    )

    visible = playable_edges_for(graph, round_, navigation)

    assert visible == ()


def test_frontier_keeps_a_forced_corridor_that_reaches_the_target() -> None:
    graph, round_ = _graph(
        (
            ("Q1", "Q2"),
            ("Q2", "Q1"),
            ("Q2", "Q3"),
            ("Q3", "Q2"),
            ("Q3", "Q4"),
        ),
        target_id="Q4",
    )
    navigation = NavigationState(
        stack=("Q1", "Q2"),
        trail=("Q1", "Q2"),
        moves=1,
    )

    visible = playable_edges_for(graph, round_, navigation)

    assert {edge.target_id for edge in visible} == {"Q3"}


def test_frontier_rejects_a_branch_when_none_of_its_choices_reach_the_target() -> None:
    graph, round_ = _graph(
        (
            ("Q1", "Q2"),
            ("Q2", "Q1"),
            ("Q2", "Q3"),
            ("Q3", "Q2"),
            ("Q3", "Q4"),
            ("Q4", "Q3"),
            ("Q4", "Q5"),
            ("Q4", "Q6"),
        ),
        target_id="Q9",
    )
    navigation = NavigationState(
        stack=("Q1", "Q2"),
        trail=("Q1", "Q2"),
        moves=1,
    )

    visible = playable_edges_for(graph, round_, navigation)

    assert visible == ()


def test_frontier_stops_when_every_choice_is_an_immediate_dead_end() -> None:
    graph, round_ = _graph(
        (("Q1", "Q2"), ("Q1", "Q3")),
        target_id="Q9",
    )

    visible = playable_edges_for(graph, round_, start_navigation("Q1"))

    assert visible == ()


def test_frontier_stops_when_every_choice_is_a_terminal_corridor() -> None:
    graph, round_ = _graph(
        (
            ("Q1", "Q2"),
            ("Q2", "Q4"),
            ("Q1", "Q3"),
            ("Q3", "Q5"),
            ("Q5", "Q6"),
        ),
        target_id="Q9",
    )

    visible = playable_edges_for(graph, round_, start_navigation("Q1"))

    assert visible == ()


def test_frontier_keeps_a_one_move_dead_end_among_real_choices() -> None:
    graph, round_ = _graph(
        (("Q1", "Q2"), ("Q1", "Q3"), ("Q3", "Q4"), ("Q4", "Q9")),
        target_id="Q9",
    )

    visible = playable_edges_for(graph, round_, start_navigation("Q1"))

    assert {edge.target_id for edge in visible} == {"Q2", "Q3"}


def test_frontier_keeps_a_route_safe_choice_beyond_the_visible_cap() -> None:
    graph, round_ = _graph(
        (
            ("Q0", "Q1"),
            ("Q0", "Q9"),
            *(("Q1", f"Q{index}") for index in range(2, 9)),
            *((f"Q{index}", "Q0") for index in range(2, 8)),
            ("Q8", "Q10"),
            ("Q10", "Q9"),
        ),
        target_id="Q9",
    )
    navigation = NavigationState(
        stack=("Q0", "Q1"),
        trail=("Q0", "Q1"),
        moves=1,
    )

    visible = playable_edges_for(graph, round_, navigation)
    visible_targets = {edge.target_id for edge in visible}

    assert len(visible_targets) == MAX_VISIBLE_TARGETS
    assert "Q8" in visible_targets
    assert "Q7" not in visible_targets


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


def _graph(
    edge_pairs: tuple[tuple[str, str], ...],
    *,
    target_id: str,
) -> tuple[MemoryGraphReader, Round]:
    entity_ids = {target_id}
    for source_id, edge_target_id in edge_pairs:
        entity_ids.update((source_id, edge_target_id))
    entities = {
        entity_id: Entity(
            id=entity_id,
            label=f"Entity {entity_id[1:]}",
            description=None,
            entity_type="item",
            category="science_technology",
        )
        for entity_id in entity_ids
    }
    edges = tuple(
        GraphEdge(
            id=f"edge-{index}",
            source_id=source_id,
            target_id=edge_target_id,
            relation_key="P361",
            relation_label="part of",
            statement_id=f"statement-{index}",
            explanation=(
                f"{entities[source_id].label} connects to {entities[edge_target_id].label}."
            ),
            target=entities[edge_target_id],
        )
        for index, (source_id, edge_target_id) in enumerate(edge_pairs)
    )
    round_ = Round(
        id="corridor-round",
        start_id="Q1",
        target_id=target_id,
        category="science_technology",
        difficulty=Difficulty.NORMAL,
        optimal_distance=3,
        time_window=180,
        published=True,
    )
    distances = _distances_to_target(round_.id, target_id, edge_pairs)
    return MemoryGraphReader(entities, edges, (round_,), distances), round_


def _distances_to_target(
    round_id: str,
    target_id: str,
    edge_pairs: tuple[tuple[str, str], ...],
) -> dict[tuple[str, str], int]:
    reverse_edges: dict[str, set[str]] = {}
    for source_id, edge_target_id in edge_pairs:
        reverse_edges.setdefault(edge_target_id, set()).add(source_id)

    distances = {target_id: 0}
    queue = deque([target_id])
    while queue:
        target = queue.popleft()
        for source_id in sorted(reverse_edges.get(target, ())):
            if source_id in distances:
                continue
            distances[source_id] = distances[target] + 1
            queue.append(source_id)
    return {(round_id, entity_id): distance for entity_id, distance in distances.items()}
