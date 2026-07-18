"""History-aware round selection shared by solo sessions and relay rooms."""

import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from webwoven_api.domain.errors import NotFoundError
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import GraphReader, Round
from webwoven_api.graph.round_eligibility import eligible_rounds


@dataclass(frozen=True, slots=True)
class RoundSelection:
    guest_id: str
    graph_version: str
    round_id: str
    category_filter: str | None
    difficulty_filter: Difficulty
    source: str
    selected_at: datetime


class RoundSelectionRepository(Protocol):
    async def list_for_guest_graph(
        self,
        guest_id: str,
        graph_version: str,
    ) -> tuple[RoundSelection, ...]: ...

    async def record(self, selection: RoundSelection) -> None: ...


RoundChooser = Callable[[Sequence[Round]], Round]


class RoundSelector:
    """Select every eligible round once per cycle before allowing repeats."""

    def __init__(
        self,
        graph: GraphReader,
        repository: RoundSelectionRepository,
        chooser: RoundChooser | None = None,
    ) -> None:
        self._graph = graph
        self._repository = repository
        self._chooser = chooser or _random_round

    async def select(
        self,
        *,
        guest_id: str,
        category: str | None,
        difficulty: Difficulty,
        source: str,
    ) -> Round:
        rounds = eligible_rounds(
            self._graph,
            self._graph.list_published_rounds(
                category=category,
                difficulty=difficulty,
            ),
        )
        if not rounds:
            raise NotFoundError(
                "No published round with multiple opening routes matches those filters"
            )
        history = await self._repository.list_for_guest_graph(
            guest_id,
            self._graph.graph_version,
        )
        selected = choose_round(rounds, tuple(item.round_id for item in history), self._chooser)
        await self._repository.record(
            RoundSelection(
                guest_id=guest_id,
                graph_version=self._graph.graph_version,
                round_id=selected.id,
                category_filter=category,
                difficulty_filter=difficulty,
                source=source,
                selected_at=datetime.now(UTC),
            )
        )
        return selected


def choose_round(
    rounds: Sequence[Round],
    chronological_history: Sequence[str],
    chooser: RoundChooser,
) -> Round:
    """Choose from the unseen portion of the current inferred selection cycle."""
    if not rounds:
        raise ValueError("rounds cannot be empty")
    eligible_ids = {round_.id for round_ in rounds}
    seen: set[str] = set()
    previous: str | None = None
    for round_id in chronological_history:
        if round_id not in eligible_ids:
            continue
        previous = round_id
        if round_id in seen:
            # Recover cleanly from legacy deterministic histories that repeated early.
            seen = {round_id}
        else:
            seen.add(round_id)
        if seen == eligible_ids:
            seen.clear()

    candidates = [round_ for round_ in rounds if round_.id not in seen]
    if not seen and previous is not None and len(candidates) > 1:
        candidates = [round_ for round_ in candidates if round_.id != previous]
    return chooser(candidates or list(rounds))


def _random_round(rounds: Sequence[Round]) -> Round:
    return secrets.choice(rounds)
