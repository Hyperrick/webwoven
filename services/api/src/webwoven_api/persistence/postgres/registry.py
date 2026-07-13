"""Immutable graph-bundle registration in PostgreSQL."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.models import GraphRegistrationRow


class PostgresGraphRegistry:
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def register(self, version: str, manifest_sha256: str) -> None:
        statement = (
            insert(GraphRegistrationRow)
            .values(
                version=version,
                manifest_sha256=manifest_sha256,
                registered_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(index_elements=[GraphRegistrationRow.version])
        )
        async with self._database.session() as session:
            await session.execute(statement)
            registered = await session.scalar(
                select(GraphRegistrationRow).where(GraphRegistrationRow.version == version)
            )
            if registered is None or registered.manifest_sha256 != manifest_sha256:
                raise RuntimeError("Graph version is already registered with another manifest")
