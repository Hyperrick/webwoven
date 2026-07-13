"""Persistence boundary owned by gameplay sessions."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from webwoven_api.sessions.models import CommandExecution, GameSession


class SessionRepository(Protocol):
    def lock(self, session_id: str) -> AbstractAsyncContextManager[None]: ...

    async def create(self, session: GameSession) -> None: ...

    async def get(self, session_id: str) -> GameSession | None: ...

    async def save(self, session: GameSession) -> None: ...

    async def get_command(self, session_id: str, command_id: str) -> CommandExecution | None: ...

    async def save_command(
        self,
        session_id: str,
        command_id: str,
        result: CommandExecution,
    ) -> None: ...
