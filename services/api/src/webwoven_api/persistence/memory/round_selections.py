"""In-memory round-selection history for local development and tests."""

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.sessions.selection import RoundSelection


class MemoryRoundSelectionRepository:
    def __init__(self) -> None:
        self._selections: list[RoundSelection] = []

    async def list_for_guest(
        self,
        guest_id: str,
        graph_version: str,
        category: str | None,
        difficulty: Difficulty,
    ) -> tuple[RoundSelection, ...]:
        return tuple(
            selection
            for selection in self._selections
            if selection.guest_id == guest_id
            and selection.graph_version == graph_version
            and selection.category_filter == category
            and selection.difficulty_filter is difficulty
        )

    async def record(self, selection: RoundSelection) -> None:
        self._selections.append(selection)
