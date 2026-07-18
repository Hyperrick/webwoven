"""History-aware selection cycles and repeat avoidance."""

import pytest
from webwoven_api.domain.scoring import TIME_WINDOWS, Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.persistence.memory.round_selections import MemoryRoundSelectionRepository
from webwoven_api.sessions.selection import RoundSelector, choose_round


def _round(round_id: str) -> Round:
    return Round(
        id=round_id,
        start_id="Q1",
        target_id="Q2",
        category="people",
        difficulty=Difficulty.NORMAL,
        optimal_distance=1,
        time_window=TIME_WINDOWS[Difficulty.NORMAL],
        published=True,
    )


def test_selects_unseen_rounds_before_starting_a_new_cycle() -> None:
    rounds = tuple(_round(round_id) for round_id in ("a", "b", "c"))
    selected = choose_round(rounds, ("a", "c"), lambda choices: choices[0])
    assert selected.id == "b"


def test_new_cycle_excludes_immediately_previous_round() -> None:
    rounds = tuple(_round(round_id) for round_id in ("a", "b", "c"))
    selected = choose_round(rounds, ("a", "b", "c"), lambda choices: choices[0])
    assert selected.id == "a"


def test_single_round_pool_can_repeat() -> None:
    only = _round("only")
    assert choose_round((only,), ("only",), lambda choices: choices[0]) is only


def test_legacy_early_repeat_starts_a_recoverable_cycle() -> None:
    rounds = tuple(_round(round_id) for round_id in ("a", "b", "c"))
    selected = choose_round(rounds, ("a", "a", "b"), lambda choices: choices[0])
    assert selected.id == "c"


@pytest.mark.asyncio
async def test_selector_keeps_round_history_when_the_category_filter_changes() -> None:
    graph = _two_round_graph()
    repository = MemoryRoundSelectionRepository()
    selector = RoundSelector(graph, repository, chooser=lambda choices: choices[0])

    first = await selector.select(
        guest_id="guest",
        category=None,
        difficulty=Difficulty.NORMAL,
        source="solo",
    )
    second = await selector.select(
        guest_id="guest",
        category="people",
        difficulty=Difficulty.NORMAL,
        source="solo",
    )

    assert first.id == "a"
    assert second.id == "b"
    history = await repository.list_for_guest_graph("guest", graph.graph_version)
    assert [item.category_filter for item in history] == [None, "people"]


def _two_round_graph() -> MemoryGraphReader:
    entities = {
        entity_id: Entity(entity_id, label, None, "person", "people")
        for entity_id, label in (
            ("A", "First start"),
            ("B", "Second start"),
            ("C", "Goal"),
            ("D", "Alternative"),
        )
    }

    def edge(edge_id: str, source_id: str, target_id: str) -> GraphEdge:
        return GraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_key="P1",
            relation_label="connects to",
            statement_id=f"statement-{edge_id}",
            explanation="Documented test connection.",
            target=entities[target_id],
        )

    rounds = (
        _round_with_start("a", "A"),
        _round_with_start("b", "B"),
    )
    return MemoryGraphReader(
        entities,
        (
            edge("A-C", "A", "C"),
            edge("A-D", "A", "D"),
            edge("B-C", "B", "C"),
            edge("B-D", "B", "D"),
        ),
        rounds,
        {
            ("a", "A"): 1,
            ("a", "C"): 0,
            ("b", "B"): 1,
            ("b", "C"): 0,
        },
    )


def _round_with_start(round_id: str, start_id: str) -> Round:
    return Round(
        id=round_id,
        start_id=start_id,
        target_id="C",
        category="people",
        difficulty=Difficulty.NORMAL,
        optimal_distance=1,
        time_window=TIME_WINDOWS[Difficulty.NORMAL],
        published=True,
    )
