"""Transactional PostgreSQL gameplay-session and command repository."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.locking import acquire_transaction_lock
from webwoven_api.persistence.postgres.models import (
    SessionCommandRow,
    SessionEventRow,
    SessionRow,
)
from webwoven_api.persistence.serialization.sessions import (
    command_execution_from_dict,
    command_execution_to_dict,
    session_from_dict,
    session_to_dict,
)
from webwoven_api.sessions.models import CommandExecution, GameSession


class PostgresSessionRepository:
    """Keep read-modify-write and command idempotency in one locked transaction."""

    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database
        self._active_transaction: ContextVar[AsyncSession | None] = ContextVar(
            "webwoven_session_transaction",
            default=None,
        )

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncGenerator[None]:
        async with self._database.session() as session:
            await acquire_transaction_lock(session, scope="game-session", identity=session_id)
            token = self._active_transaction.set(session)
            try:
                yield
            finally:
                self._active_transaction.reset(token)

    async def create(self, session: GameSession) -> None:
        async with self._database.session() as transaction:
            transaction.add(_row_from_session(session))

    async def get(self, session_id: str) -> GameSession | None:
        active = self._active_transaction.get()
        if active is not None:
            return await _get_session(active, session_id)
        async with self._database.session() as session:
            return await _get_session(session, session_id)

    async def save(self, session: GameSession) -> None:
        active = self._active_transaction.get()
        if active is not None:
            await _save_session(active, session)
            return
        async with self._database.session() as transaction:
            await _save_session(transaction, session)

    async def get_command(self, session_id: str, command_id: str) -> CommandExecution | None:
        active = self._active_transaction.get()
        if active is not None:
            return await _get_command(active, session_id, command_id)
        async with self._database.session() as session:
            return await _get_command(session, session_id, command_id)

    async def save_command(
        self,
        session_id: str,
        command_id: str,
        result: CommandExecution,
    ) -> None:
        active = self._active_transaction.get()
        if active is None:
            raise RuntimeError("save_command must run inside the session lock transaction")
        _add_command(active, session_id, command_id, result)


async def _get_session(session: AsyncSession, session_id: str) -> GameSession | None:
    row = await session.scalar(select(SessionRow).where(SessionRow.id == session_id))
    return session_from_dict(row.state_json) if row is not None else None


async def _save_session(session: AsyncSession, game_session: GameSession) -> None:
    row = await session.scalar(select(SessionRow).where(SessionRow.id == game_session.id))
    if row is None:
        session.add(_row_from_session(game_session))
        return
    row.graph_version = game_session.graph_version
    row.round_id = game_session.round.id
    row.mode = game_session.mode.value
    row.status = game_session.status.value
    row.state_version = game_session.state_version
    row.state_json = _json_document(session_to_dict(game_session))
    row.started_at = game_session.started_at
    row.completed_at = game_session.completed_at
    row.final_score = game_session.final_score


async def _get_command(
    session: AsyncSession, session_id: str, command_id: str
) -> CommandExecution | None:
    row = await session.scalar(
        select(SessionCommandRow).where(
            SessionCommandRow.session_id == session_id,
            SessionCommandRow.client_command_id == command_id,
        )
    )
    return command_execution_from_dict(row.result_json) if row is not None else None


def _add_command(
    session: AsyncSession,
    session_id: str,
    command_id: str,
    result: CommandExecution,
) -> None:
    now = datetime.now(UTC)
    result_document = _json_document(command_execution_to_dict(result))
    session.add(
        SessionCommandRow(
            session_id=session_id,
            client_command_id=command_id,
            expected_state_version=max(result.session.state_version - 1, 0),
            result_json=result_document,
            created_at=now,
        )
    )
    session.add(
        SessionEventRow(
            session_id=session_id,
            event_type="command.applied",
            state_version=result.session.state_version,
            payload_json={"client_command_id": command_id, "result": result_document},
            created_at=now,
        )
    )


def _row_from_session(game_session: GameSession) -> SessionRow:
    return SessionRow(
        id=game_session.id,
        guest_id=game_session.guest_id,
        graph_version=game_session.graph_version,
        round_id=game_session.round.id,
        mode=game_session.mode.value,
        status=game_session.status.value,
        state_version=game_session.state_version,
        state_json=_json_document(session_to_dict(game_session)),
        started_at=game_session.started_at,
        completed_at=game_session.completed_at,
        final_score=game_session.final_score,
    )


def _json_document(value: dict[str, object]) -> dict[str, Any]:
    return cast(dict[str, Any], value)
