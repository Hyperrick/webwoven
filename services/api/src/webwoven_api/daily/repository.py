"""Persistence boundary owned by Daily Connection."""

from datetime import date
from typing import Protocol

from webwoven_api.daily.models import DailyAssignment, DailyScore, RankedDailyScore


class DailyRepository(Protocol):
    async def get_assignment(self, day: date) -> DailyAssignment | None: ...

    async def save_assignment(self, assignment: DailyAssignment) -> None: ...

    async def save_score(self, score: DailyScore) -> None: ...

    async def list_scores(self, day: date, limit: int) -> tuple[DailyScore, ...]: ...

    async def get_ranked_score(self, day: date, guest_id: str) -> RankedDailyScore | None: ...
