"""Daily Connection and leaderboard wire contracts."""

from datetime import date, datetime

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.http.contracts.common import ApiModel, EntityResponse


class DailyResponse(ApiModel):
    day: date
    graph_version: str
    round_id: str
    category: str
    difficulty: Difficulty
    optimal_distance: int
    time_window: int
    start: EntityResponse
    target: EntityResponse


class LeaderboardEntry(ApiModel):
    rank: int
    display_name: str
    score: int
    moves: int
    hints_used: int
    elapsed_seconds: float
    completed_at: datetime


class DailyLeaderboardResponse(ApiModel):
    day: date
    entries: list[LeaderboardEntry]
