"""PostgreSQL round-selection history adapter."""

from sqlalchemy import select

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.models import RoundSelectionRow
from webwoven_api.sessions.selection import RoundSelection


class PostgresRoundSelectionRepository:
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def list_for_guest_graph(
        self,
        guest_id: str,
        graph_version: str,
    ) -> tuple[RoundSelection, ...]:
        async with self._database.session() as session:
            rows = (
                await session.scalars(
                    select(RoundSelectionRow)
                    .where(
                        RoundSelectionRow.guest_id == guest_id,
                        RoundSelectionRow.graph_version == graph_version,
                    )
                    .order_by(RoundSelectionRow.selected_at, RoundSelectionRow.id)
                )
            ).all()
        return tuple(
            RoundSelection(
                guest_id=row.guest_id,
                graph_version=row.graph_version,
                round_id=row.round_id,
                category_filter=row.category_filter,
                difficulty_filter=Difficulty(row.difficulty_filter),
                source=row.source,
                selected_at=row.selected_at,
            )
            for row in rows
        )

    async def record(self, selection: RoundSelection) -> None:
        async with self._database.session() as session:
            session.add(
                RoundSelectionRow(
                    guest_id=selection.guest_id,
                    graph_version=selection.graph_version,
                    round_id=selection.round_id,
                    category_filter=selection.category_filter,
                    difficulty_filter=selection.difficulty_filter.value,
                    source=selection.source,
                    selected_at=selection.selected_at,
                )
            )
