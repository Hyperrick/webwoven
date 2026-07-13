"""First-party pseudonymous analytics event sink."""

from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.models import AnalyticsEventRow


class PostgresAnalyticsRepository:
    """Store product events only; callers must never pass network identifiers."""

    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def record(
        self,
        *,
        pseudonymous_guest_id: str | None,
        event_name: str,
        properties: dict[str, object],
        occurred_at: datetime,
    ) -> None:
        async with self._database.session() as session:
            session.add(
                AnalyticsEventRow(
                    id=str(uuid4()),
                    pseudonymous_guest_id=pseudonymous_guest_id,
                    event_name=event_name,
                    properties_json=cast(dict[str, Any], properties),
                    occurred_at=occurred_at,
                )
            )
