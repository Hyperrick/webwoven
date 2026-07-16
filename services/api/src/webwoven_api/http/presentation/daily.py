"""Daily assignment and leaderboard wire presentation."""

from datetime import date

from webwoven_api.daily.models import DailyAssignment, DailyScore, RankedDailyScore
from webwoven_api.graph.contracts import GraphReader, Round
from webwoven_api.http.contracts.daily import (
    DailyLeaderboardResponse,
    DailyResponse,
    LeaderboardEntry,
)
from webwoven_api.http.presentation.entities import entity_response


def daily_response(assignment: DailyAssignment, round_: Round, graph: GraphReader) -> DailyResponse:
    start = graph.get_entity(round_.start_id)
    target = graph.get_entity(round_.target_id)
    if start is None or target is None:
        raise RuntimeError("Daily round references a missing entity")
    return DailyResponse(
        day=assignment.day,
        graph_version=assignment.graph_version,
        round_id=round_.id,
        category=round_.category,
        difficulty=round_.difficulty,
        optimal_distance=round_.optimal_distance,
        time_window=round_.time_window,
        start=entity_response(start),
        target=entity_response(target),
    )


def leaderboard_response(
    day: date,
    scores: tuple[DailyScore, ...],
    current_guest_id: str | None,
    current_guest: RankedDailyScore | None,
) -> DailyLeaderboardResponse:
    return DailyLeaderboardResponse(
        day=day,
        entries=[
            _leaderboard_entry(score, index, score.guest_id == current_guest_id)
            for index, score in enumerate(scores, start=1)
        ],
        current_guest_entry=(
            _leaderboard_entry(current_guest.score, current_guest.rank, True)
            if current_guest is not None
            else None
        ),
    )


def _leaderboard_entry(score: DailyScore, rank: int, is_current_guest: bool) -> LeaderboardEntry:
    return LeaderboardEntry(
        rank=rank,
        display_name=score.display_name,
        score=score.score,
        moves=score.moves,
        hints_used=score.hints_used,
        elapsed_seconds=score.elapsed_seconds,
        completed_at=score.completed_at,
        is_current_guest=is_current_guest,
    )
