"""Daily Connection assignment and leaderboard routes."""

from datetime import UTC, date, datetime

from fastapi import APIRouter, Query

from webwoven_api.http.contracts.daily import DailyLeaderboardResponse, DailyResponse
from webwoven_api.http.dependencies import ContainerDependency, OptionalGuestDependency
from webwoven_api.http.presentation.daily import daily_response, leaderboard_response

router = APIRouter(prefix="/api/v1", tags=["daily"])


@router.get("/daily", response_model=DailyResponse)
async def get_daily(container: ContainerDependency) -> DailyResponse:
    assignment, round_ = await container.daily.assignment()
    return daily_response(assignment, round_, container.graph)


@router.get("/leaderboards/daily", response_model=DailyLeaderboardResponse)
async def get_daily_leaderboard(
    container: ContainerDependency,
    guest: OptionalGuestDependency,
    day: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> DailyLeaderboardResponse:
    target_day = day or datetime.now(UTC).date()
    guest_id = guest.id if guest is not None else None
    scores, current = await container.daily.leaderboard(target_day, limit=limit, guest_id=guest_id)
    return leaderboard_response(target_day, scores, guest_id, current)
