"""PostgreSQL UTC Daily assignment and ranked-score repository."""

from datetime import date, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.elements import ColumnElement

from webwoven_api.daily.models import DailyAssignment, DailyScore, RankedDailyScore
from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.locking import acquire_transaction_lock
from webwoven_api.persistence.postgres.models import DailyAssignmentRow, DailyScoreRow, GuestRow


class PostgresDailyRepository:
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def get_assignment(self, day: date) -> DailyAssignment | None:
        async with self._database.session() as session:
            row = await session.scalar(
                select(DailyAssignmentRow).where(DailyAssignmentRow.day == day)
            )
            return assignment_from_row(row) if row is not None else None

    async def save_assignment(self, assignment: DailyAssignment) -> None:
        statement = (
            insert(DailyAssignmentRow)
            .values(
                day=assignment.day,
                graph_version=assignment.graph_version,
                round_id=assignment.round_id,
            )
            .on_conflict_do_nothing(index_elements=[DailyAssignmentRow.day])
        )
        async with self._database.session() as session:
            await session.execute(statement)

    async def save_score(self, score: DailyScore) -> None:
        async with self._database.session() as session:
            await acquire_transaction_lock(
                session,
                scope="daily-score",
                identity=f"{score.day.isoformat()}:{score.guest_id}",
            )
            current = await session.scalar(
                select(DailyScoreRow).where(
                    DailyScoreRow.day == score.day,
                    DailyScoreRow.guest_id == score.guest_id,
                )
            )
            if current is not None and _row_rank_key(current) <= _score_rank_key(score):
                return
            if current is None:
                session.add(_row_from_score(score))
                return
            _copy_score(current, score)

    async def list_scores(self, day: date, limit: int) -> tuple[DailyScore, ...]:
        statement = (
            select(DailyScoreRow, GuestRow.display_name)
            .join(GuestRow, GuestRow.id == DailyScoreRow.guest_id)
            .where(DailyScoreRow.day == day)
            .order_by(
                DailyScoreRow.score.desc(),
                DailyScoreRow.elapsed_ms.asc(),
                DailyScoreRow.moves.asc(),
                DailyScoreRow.completed_at.asc(),
                DailyScoreRow.guest_id.asc(),
            )
            .limit(limit)
        )
        async with self._database.session() as session:
            results = (await session.execute(statement)).all()
        return tuple(score_from_row(row, display_name) for row, display_name in results)

    async def get_ranked_score(self, day: date, guest_id: str) -> RankedDailyScore | None:
        current_statement = (
            select(DailyScoreRow, GuestRow.display_name)
            .join(GuestRow, GuestRow.id == DailyScoreRow.guest_id)
            .where(DailyScoreRow.day == day, DailyScoreRow.guest_id == guest_id)
        )
        async with self._database.session() as session:
            current = (await session.execute(current_statement)).one_or_none()
            if current is None:
                return None
            row, display_name = current
            better_count = await session.scalar(
                select(func.count())
                .select_from(DailyScoreRow)
                .where(DailyScoreRow.day == day, _ranks_before(row))
            )
        return RankedDailyScore(
            rank=int(better_count or 0) + 1,
            score=score_from_row(row, display_name),
        )


def assignment_from_row(row: DailyAssignmentRow) -> DailyAssignment:
    return DailyAssignment(day=row.day, graph_version=row.graph_version, round_id=row.round_id)


def score_from_row(row: DailyScoreRow, display_name: str) -> DailyScore:
    return DailyScore(
        day=row.day,
        session_id=row.session_id,
        guest_id=row.guest_id,
        display_name=display_name,
        score=row.score,
        moves=row.moves,
        hints_used=row.hints_used,
        elapsed_seconds=row.elapsed_ms / 1000,
        completed_at=row.completed_at,
    )


def _row_from_score(score: DailyScore) -> DailyScoreRow:
    return DailyScoreRow(
        day=score.day,
        session_id=score.session_id,
        guest_id=score.guest_id,
        score=score.score,
        moves=score.moves,
        hints_used=score.hints_used,
        elapsed_ms=round(score.elapsed_seconds * 1000),
        completed_at=score.completed_at,
    )


def _copy_score(row: DailyScoreRow, score: DailyScore) -> None:
    row.session_id = score.session_id
    row.score = score.score
    row.moves = score.moves
    row.hints_used = score.hints_used
    row.elapsed_ms = round(score.elapsed_seconds * 1000)
    row.completed_at = score.completed_at


def _score_rank_key(score: DailyScore) -> tuple[int, int, int, datetime, str]:
    return (
        -score.score,
        round(score.elapsed_seconds * 1000),
        score.moves,
        score.completed_at,
        score.guest_id,
    )


def _row_rank_key(row: DailyScoreRow) -> tuple[int, int, int, datetime, str]:
    return (-row.score, row.elapsed_ms, row.moves, row.completed_at, row.guest_id)


def _ranks_before(current: DailyScoreRow) -> ColumnElement[bool]:
    same_score = DailyScoreRow.score == current.score
    same_time = same_score & (DailyScoreRow.elapsed_ms == current.elapsed_ms)
    same_moves = same_time & (DailyScoreRow.moves == current.moves)
    same_completion = same_moves & (DailyScoreRow.completed_at == current.completed_at)
    return or_(
        DailyScoreRow.score > current.score,
        and_(same_score, DailyScoreRow.elapsed_ms < current.elapsed_ms),
        and_(same_time, DailyScoreRow.moves < current.moves),
        and_(same_moves, DailyScoreRow.completed_at < current.completed_at),
        and_(same_completion, DailyScoreRow.guest_id < current.guest_id),
    )
