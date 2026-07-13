"""Adapter from completed Daily sessions into the Daily leaderboard."""

from webwoven_api.daily.models import DailyScore
from webwoven_api.daily.service import DailyService
from webwoven_api.guests.service import GuestService
from webwoven_api.sessions.models import GameSession, SessionMode


class DailyCompletionRecorder:
    def __init__(self, daily: DailyService, guests: GuestService) -> None:
        self._daily = daily
        self._guests = guests

    async def record_completion(self, session: GameSession, elapsed_seconds: float) -> None:
        if session.mode is not SessionMode.DAILY:
            return
        if session.completed_at is None or session.final_score is None:
            return
        guest = await self._guests.get(session.guest_id)
        await self._daily.record(
            DailyScore(
                day=session.daily_day or session.completed_at.date(),
                session_id=session.id,
                guest_id=session.guest_id,
                display_name=guest.display_name,
                score=session.final_score,
                moves=session.navigation.moves,
                hints_used=len(session.hints),
                elapsed_seconds=elapsed_seconds,
                completed_at=session.completed_at,
            )
        )
