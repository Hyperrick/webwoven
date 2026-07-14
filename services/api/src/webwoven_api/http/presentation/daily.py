"""Daily assignment and leaderboard wire presentation."""

from datetime import date

from webwoven_api.daily.models import DailyAssignment, DailyScore
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


def leaderboard_response(day: date, scores: tuple[DailyScore, ...]) -> DailyLeaderboardResponse:
    return DailyLeaderboardResponse(
        day=day,
        entries=[
            LeaderboardEntry(
                rank=index,
                display_name=score.display_name,
                score=score.score,
                moves=score.moves,
                hints_used=score.hints_used,
                elapsed_seconds=score.elapsed_seconds,
                completed_at=score.completed_at,
            )
            for index, score in enumerate(scores, start=1)
        ],
    )
