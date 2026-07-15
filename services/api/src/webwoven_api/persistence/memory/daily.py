"""In-memory UTC Daily assignments and best-per-guest scores."""

import asyncio
from dataclasses import replace
from datetime import date, datetime

from webwoven_api.daily.models import DailyAssignment, DailyScore, RankedDailyScore
from webwoven_api.guests.repository import GuestRepository


class MemoryDailyRepository:
    def __init__(self, guests: GuestRepository) -> None:
        self._guests = guests
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
        ranked = sorted(scores, key=_rank_key)[:limit]
        return tuple([await self._with_current_name(score) for score in ranked])

    async def get_ranked_score(self, day: date, guest_id: str) -> RankedDailyScore | None:
        async with self._lock:
            scores = [score for score in self._scores.values() if score.day == day]
        for rank, score in enumerate(sorted(scores, key=_rank_key), start=1):
            if score.guest_id == guest_id:
                return RankedDailyScore(rank, await self._with_current_name(score))
        return None

    async def _with_current_name(self, score: DailyScore) -> DailyScore:
        guest = await self._guests.get(score.guest_id)
        return replace(score, display_name=guest.display_name) if guest is not None else score


def _rank_key(score: DailyScore) -> tuple[int, float, int, datetime, str]:
    return (
        -score.score,
        score.elapsed_seconds,
        score.moves,
        score.completed_at,
        score.guest_id,
    )
