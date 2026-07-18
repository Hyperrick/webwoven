"""Concurrency-safe in-memory Live Relay repository."""

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from webwoven_api.rooms.models import Room


class MemoryRoomRepository:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._create_lock = asyncio.Lock()

    @asynccontextmanager
    async def lock(self, code: str) -> AsyncGenerator[None]:
        async with self._locks[code]:
            yield

    async def create(self, room: Room) -> bool:
        async with self._create_lock:
            if room.code in self._rooms:
                return False
            self._rooms[room.code] = room
            return True

    async def get(self, code: str) -> Room | None:
        return self._rooms.get(code)

    async def save(self, room: Room) -> None:
        self._rooms[room.code] = room

    async def find_by_session(self, session_id: str) -> Room | None:
        return next(
            (
                room
                for room in self._rooms.values()
                if any(
                    participant.active and participant.session_id == session_id
                    for participant in room.participants
                )
            ),
            None,
        )
