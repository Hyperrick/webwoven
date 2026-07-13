"""PostgreSQL engine lifecycle and transaction ownership."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from webwoven_api.persistence.postgres.models import Base


class PostgresDatabase:
    def __init__(self, database_url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        self._sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        async with self._sessions() as session, session.begin():
            yield session

    async def create_schema(self) -> None:
        """Create absent tables in one DDL transaction; existing tables are untouched."""
        async with self.engine.begin() as connection:
            await connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": 8_909_638_271_872_211_725},
            )
            await connection.run_sync(Base.metadata.create_all)

    async def ping(self) -> bool:
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return False
        return True

    async def close(self) -> None:
        await self.engine.dispose()
