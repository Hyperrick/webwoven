"""Boundary for mode owners to authorize session commands."""

from typing import Protocol

from webwoven_api.sessions.models import GameSession


class SessionCommandAuthorizer(Protocol):
    async def authorize(self, session: GameSession) -> None: ...


class AllowSessionCommands:
    async def authorize(self, session: GameSession) -> None:
        del session
