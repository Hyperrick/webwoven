"""Automatic round pools exclude starts that offer no meaningful choice."""

from datetime import date

import pytest
from webwoven_api.daily.models import DailyAssignment
from webwoven_api.daily.service import DailyService
from webwoven_api.domain.errors import NotFoundError
from webwoven_api.domain.scoring import TIME_WINDOWS, Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.graph.round_eligibility import eligible_rounds, has_multiple_opening_routes
from webwoven_api.persistence.memory.daily import MemoryDailyRepository
from webwoven_api.persistence.memory.guests import MemoryGuestRepository
from webwoven_api.persistence.memory.round_selections import MemoryRoundSelectionRepository
from webwoven_api.sessions.selection import RoundSelector


def test_eligibility_counts_distinct_opening_targets() -> None:
    graph, forced, choice = _graph()

    assert has_multiple_opening_routes(graph, forced) is False
    assert has_multiple_opening_routes(graph, choice) is True
    assert eligible_rounds(graph, (forced, choice)) == (choice,)


@pytest.mark.asyncio
async def test_automatic_selection_excludes_forced_openings() -> None:
    graph, forced, choice = _graph()
    selector = RoundSelector(
        graph,
        MemoryRoundSelectionRepository(),
        chooser=lambda rounds: rounds[0],
    )

    selected = await selector.select(
        guest_id="guest",
        category=None,
        difficulty=Difficulty.NORMAL,
        source="solo",
    )

    assert selected is choice
    assert selected is not forced


@pytest.mark.asyncio
async def test_automatic_selection_fails_when_every_opening_is_forced() -> None:
    graph, forced, _ = _graph()
    forced_only = MemoryGraphReader(
        graph.entities,
        graph.edges,
        (forced,),
        graph.distances,
    )
    selector = RoundSelector(
        forced_only,
        MemoryRoundSelectionRepository(),
        chooser=lambda rounds: rounds[0],
    )

    with pytest.raises(NotFoundError, match="multiple opening routes"):
        await selector.select(
            guest_id="guest",
            category=None,
            difficulty=Difficulty.NORMAL,
            source="solo",
        )


@pytest.mark.asyncio
async def test_new_daily_assignments_use_the_same_eligible_pool() -> None:
    graph, forced, choice = _graph()
    repository = MemoryDailyRepository(MemoryGuestRepository())
    service = DailyService(graph, repository)

    assignment, selected = await service.assignment(date(2026, 7, 16))

    assert assignment.round_id == choice.id
    assert selected is choice
    assert selected is not forced


@pytest.mark.asyncio
async def test_existing_daily_assignment_remains_pinned() -> None:
    graph, forced, _ = _graph()
    repository = MemoryDailyRepository(MemoryGuestRepository())
    day = date(2026, 7, 16)
    await repository.save_assignment(DailyAssignment(day, graph.graph_version, forced.id))

    assignment, selected = await DailyService(graph, repository).assignment(day)

    assert assignment.round_id == forced.id
    assert selected is forced


def _graph() -> tuple[MemoryGraphReader, Round, Round]:
    entities = {
        entity_id: Entity(entity_id, label, None, "person", "people")
        for entity_id, label in (
            ("A", "Forced start"),
            ("B", "Only opening"),
            ("C", "Choice start"),
            ("D", "Goal"),
            ("E", "Alternative"),
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

    forced = _round("forced", "A")
    choice = _round("choice", "C")
    graph = MemoryGraphReader(
        entities,
        (
            edge("A-B-1", "A", "B"),
            edge("A-B-2", "A", "B"),
            edge("B-D", "B", "D"),
            edge("C-D", "C", "D"),
            edge("C-E", "C", "E"),
        ),
        (forced, choice),
        {
            (forced.id, "A"): 2,
            (forced.id, "B"): 1,
            (forced.id, "D"): 0,
            (choice.id, "C"): 1,
            (choice.id, "D"): 0,
            (choice.id, "E"): 2,
        },
    )
    return graph, forced, choice


def _round(round_id: str, start_id: str) -> Round:
    return Round(
        id=round_id,
        start_id=start_id,
        target_id="D",
        category="people",
        difficulty=Difficulty.NORMAL,
        optimal_distance=1,
        time_window=TIME_WINDOWS[Difficulty.NORMAL],
        published=True,
    )
