"""In-memory session repository with per-session command serialization."""

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from webwoven_api.sessions.models import CommandExecution, GameSession


class MemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, GameSession] = {}
        self._commands: dict[tuple[str, str], CommandExecution] = {}
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncGenerator[None]:
        async with self._locks[session_id]:
            yield

    async def create(self, session: GameSession) -> None:
        self._sessions[session.id] = session

    async def get(self, session_id: str) -> GameSession | None:
        return self._sessions.get(session_id)

    async def save(self, session: GameSession) -> None:
        self._sessions[session.id] = session

    async def get_command(self, session_id: str, command_id: str) -> CommandExecution | None:
        return self._commands.get((session_id, command_id))

    async def save_command(
        self,
        session_id: str,
        command_id: str,
        result: CommandExecution,
    ) -> None:
        self._commands[(session_id, command_id)] = result
