"""Fan-out boundary for transient room events."""

import asyncio
from collections import defaultdict
from contextlib import suppress
from typing import Protocol

from webwoven_api.rooms.models import RoomEvent


class RoomEventBroker(Protocol):
    async def publish(self, room_code: str, event: RoomEvent) -> None: ...

    async def subscribe(self, room_code: str) -> asyncio.Queue[RoomEvent]: ...

    async def unsubscribe(self, room_code: str, queue: asyncio.Queue[RoomEvent]) -> None: ...


class MemoryRoomEventBroker:
    def __init__(self) -> None:
        self._subscribers: defaultdict[str, set[asyncio.Queue[RoomEvent]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def publish(self, room_code: str, event: RoomEvent) -> None:
        async with self._lock:
            queues = tuple(self._subscribers.get(room_code, ()))
        for queue in queues:
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(event)

    async def subscribe(self, room_code: str) -> asyncio.Queue[RoomEvent]:
        queue: asyncio.Queue[RoomEvent] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[room_code].add(queue)
        return queue

    async def unsubscribe(self, room_code: str, queue: asyncio.Queue[RoomEvent]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(room_code)
            if subscribers is None:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(room_code, None)
