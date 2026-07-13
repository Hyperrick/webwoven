"""PostgreSQL moderation-report sink."""

from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.models import ContentReportRow
from webwoven_api.reports.models import ContentReport


class PostgresContentReportRepository:
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def create(self, report: ContentReport) -> None:
        async with self._database.session() as session:
            session.add(
                ContentReportRow(
                    id=report.id,
                    guest_id=report.guest_id,
                    entity_id=report.entity_id,
                    edge_id=report.edge_id,
                    round_id=report.round_id,
                    reason=report.reason,
                    details=report.details,
                    created_at=report.created_at,
                )
            )
