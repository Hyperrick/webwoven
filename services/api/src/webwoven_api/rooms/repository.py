"""Persistence boundary owned by Live Relay rooms."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from webwoven_api.rooms.models import Room


class RoomRepository(Protocol):
    def lock(self, code: str) -> AbstractAsyncContextManager[None]: ...

    async def create(self, room: Room) -> bool: ...

    async def get(self, code: str) -> Room | None: ...

    async def save(self, room: Room) -> None: ...

    async def find_by_session(self, session_id: str) -> Room | None: ...
