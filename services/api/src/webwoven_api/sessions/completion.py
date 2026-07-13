"""Boundary for durable work triggered by a completed session."""

from typing import Protocol

from webwoven_api.sessions.models import GameSession


class SessionCompletionRecorder(Protocol):
    async def record_completion(self, session: GameSession, elapsed_seconds: float) -> None: ...


class NullCompletionRecorder:
    async def record_completion(self, session: GameSession, elapsed_seconds: float) -> None:
        del session, elapsed_seconds
