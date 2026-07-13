"""Valkey Streams plus Pub/Sub fan-out for ordered room events."""

import asyncio
import json
from contextlib import suppress
from dataclasses import dataclass

from webwoven_api.persistence.serialization.rooms import (
    room_event_from_dict,
    room_event_to_dict,
)
from webwoven_api.persistence.serialization.values import PersistenceDataError
from webwoven_api.persistence.valkey.client import ValkeyClient, ValkeySubscription
from webwoven_api.persistence.valkey.keys import ValkeyKeys
from webwoven_api.rooms.models import RoomEvent


@dataclass(slots=True)
class _Subscriber:
    subscription: ValkeySubscription
    task: asyncio.Task[None]


class ValkeyRoomEventBroker:
    def __init__(
        self,
        client: ValkeyClient,
        *,
        stream_max_length: int,
        stream_ttl_seconds: int,
    ) -> None:
        self._client = client
        self._stream_max_length = stream_max_length
        self._stream_ttl_seconds = stream_ttl_seconds
        self._subscribers: dict[asyncio.Queue[RoomEvent], _Subscriber] = {}
        self._guard = asyncio.Lock()

    async def publish(self, room_code: str, event: RoomEvent) -> None:
        code = room_code.upper()
        payload = _encode_event(event)
        stream = ValkeyKeys.room_events(code)
        await self._client.append_event(
            stream,
            {
                "sequence": str(event.sequence),
                "type": event.type,
                "event": payload,
            },
            max_length=self._stream_max_length,
        )
        await self._client.expire(stream, self._stream_ttl_seconds)
        await self._client.publish(ValkeyKeys.room_channel(code), payload)

    async def subscribe(self, room_code: str) -> asyncio.Queue[RoomEvent]:
        queue: asyncio.Queue[RoomEvent] = asyncio.Queue(maxsize=100)
        subscription = await self._client.open_subscription(
            ValkeyKeys.room_channel(room_code.upper())
        )
        task = asyncio.create_task(self._relay(subscription, queue))
        async with self._guard:
            self._subscribers[queue] = _Subscriber(subscription, task)
        return queue

    async def unsubscribe(
        self,
        room_code: str,
        queue: asyncio.Queue[RoomEvent],
    ) -> None:
        del room_code
        async with self._guard:
            subscriber = self._subscribers.pop(queue, None)
        if subscriber is None:
            return
        subscriber.task.cancel()
        with suppress(asyncio.CancelledError):
            await subscriber.task
        await subscriber.subscription.close()

    async def close(self) -> None:
        async with self._guard:
            queues = tuple(self._subscribers)
        for queue in queues:
            await self.unsubscribe("", queue)

    async def _relay(
        self,
        subscription: ValkeySubscription,
        queue: asyncio.Queue[RoomEvent],
    ) -> None:
        while True:
            raw = await subscription.next_message(timeout_seconds=1)
            if raw is None:
                continue
            try:
                event = _decode_event(raw)
            except (json.JSONDecodeError, PersistenceDataError, ValueError):
                continue
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(event)


def _encode_event(event: RoomEvent) -> str:
    return json.dumps(room_event_to_dict(event), separators=(",", ":"), sort_keys=True)


def _decode_event(raw: str) -> RoomEvent:
    return room_event_from_dict(json.loads(raw))
