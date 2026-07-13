"""In-memory UTC Daily assignments and best-per-guest scores."""

import asyncio
from datetime import date, datetime

from webwoven_api.daily.models import DailyAssignment, DailyScore


class MemoryDailyRepository:
    def __init__(self) -> None:
        self._assignments: dict[date, DailyAssignment] = {}
        self._scores: dict[tuple[date, str], DailyScore] = {}
        self._lock = asyncio.Lock()

    async def get_assignment(self, day: date) -> DailyAssignment | None:
        async with self._lock:
            return self._assignments.get(day)

    async def save_assignment(self, assignment: DailyAssignment) -> None:
        async with self._lock:
            self._assignments.setdefault(assignment.day, assignment)

    async def save_score(self, score: DailyScore) -> None:
        key = (score.day, score.guest_id)
        async with self._lock:
            current = self._scores.get(key)
            if current is None or _rank_key(score) < _rank_key(current):
                self._scores[key] = score

    async def list_scores(self, day: date, limit: int) -> tuple[DailyScore, ...]:
        async with self._lock:
            scores = [score for score in self._scores.values() if score.day == day]
        return tuple(sorted(scores, key=_rank_key)[:limit])


def _rank_key(score: DailyScore) -> tuple[int, float, int, datetime]:

    return (-score.score, score.elapsed_seconds, score.moves, score.completed_at)
