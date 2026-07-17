"""UTC Daily assignment and leaderboard ordering."""

import hashlib
from datetime import UTC, date, datetime

from webwoven_api.daily.models import DailyAssignment, DailyScore, RankedDailyScore
from webwoven_api.daily.repository import DailyRepository
from webwoven_api.domain.errors import NotFoundError
from webwoven_api.graph.contracts import GraphReader, Round
from webwoven_api.graph.round_eligibility import eligible_rounds


class DailyService:
    def __init__(self, graph: GraphReader, repository: DailyRepository) -> None:
        self._graph = graph
        self._repository = repository

    async def assignment(self, day: date | None = None) -> tuple[DailyAssignment, Round]:
        target_day = day or datetime.now(UTC).date()
        existing = await self._repository.get_assignment(target_day)
        if existing is not None:
            round_ = self._graph.get_round(existing.round_id)
            if round_ is None:
                raise NotFoundError("Pinned Daily round is missing from this graph")
            return existing, round_

        rounds = eligible_rounds(self._graph, self._graph.list_published_rounds())
        if not rounds:
            raise NotFoundError("No published rounds with multiple opening routes are available")
        digest = hashlib.sha256(
            f"{target_day.isoformat()}:{self._graph.graph_version}".encode()
        ).digest()
        round_ = rounds[int.from_bytes(digest[:8], "big") % len(rounds)]
        assignment = DailyAssignment(target_day, self._graph.graph_version, round_.id)
        await self._repository.save_assignment(assignment)
        return assignment, round_

    async def record(self, score: DailyScore) -> None:
        await self._repository.save_score(score)

    async def leaderboard(
        self,
        day: date | None = None,
        *,
        limit: int = 20,
        guest_id: str | None = None,
    ) -> tuple[tuple[DailyScore, ...], RankedDailyScore | None]:
        target_day = day or datetime.now(UTC).date()
        scores = await self._repository.list_scores(target_day, min(max(limit, 1), 100))
        current = (
            await self._repository.get_ranked_score(target_day, guest_id)
            if guest_id is not None
            else None
        )
        return scores, current
