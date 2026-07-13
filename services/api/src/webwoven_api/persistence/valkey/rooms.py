"""Valkey active-room snapshots, reconnect indices, TTLs, and distributed locks."""

import json
from contextlib import AbstractAsyncContextManager
from typing import Protocol

from webwoven_api.persistence.serialization.rooms import room_from_dict, room_to_dict
from webwoven_api.persistence.valkey.client import ValkeyClient
from webwoven_api.persistence.valkey.keys import ValkeyKeys
from webwoven_api.persistence.valkey.locks import ValkeyLockManager
from webwoven_api.rooms.models import Room, RoomState


class CompletedRoomArchive(Protocol):
    async def archive(self, room: Room) -> None: ...


class ValkeyRoomRepository:
    def __init__(
        self,
        client: ValkeyClient,
        archive: CompletedRoomArchive,
        *,
        active_ttl_seconds: int,
        completed_ttl_seconds: int,
        lock_lease_seconds: int,
        lock_wait_seconds: float,
    ) -> None:
        self._client = client
        self._archive = archive
        self._active_ttl_seconds = active_ttl_seconds
        self._completed_ttl_seconds = completed_ttl_seconds
        self._locks = ValkeyLockManager(
            client,
            lease_seconds=lock_lease_seconds,
            wait_seconds=lock_wait_seconds,
        )

    def lock(self, code: str) -> AbstractAsyncContextManager[None]:
        return self._locks.lock(ValkeyKeys.room_lock(code.upper()))

    async def create(self, room: Room) -> bool:
        return await self._client.set(
            ValkeyKeys.room(room.code),
            _encode_room(room),
            ttl_seconds=self._active_ttl_seconds,
            only_if_absent=True,
        )

    async def get(self, code: str) -> Room | None:
        raw = await self._client.get(ValkeyKeys.room(code.upper()))
        return _decode_room(raw) if raw is not None else None

    async def save(self, room: Room) -> None:
        ttl = self._ttl_for(room)
        await self._client.set(
            ValkeyKeys.room(room.code),
            _encode_room(room),
            ttl_seconds=ttl,
        )
        for participant in room.participants:
            if participant.session_id is not None:
                await self._client.set(
                    ValkeyKeys.session_room(participant.session_id),
                    room.code,
                    ttl_seconds=ttl,
                )
        if room.state in {RoomState.FINISHED, RoomState.CLOSED}:
            await self._archive.archive(room)

    async def find_by_session(self, session_id: str) -> Room | None:
        code = await self._client.get(ValkeyKeys.session_room(session_id))
        return await self.get(code) if code is not None else None

    def _ttl_for(self, room: Room) -> int:
        if room.state in {RoomState.FINISHED, RoomState.CLOSED}:
            return self._completed_ttl_seconds
        return self._active_ttl_seconds


def _encode_room(room: Room) -> str:
    return json.dumps(room_to_dict(room), separators=(",", ":"), sort_keys=True)


def _decode_room(raw: str) -> Room:
    return room_from_dict(json.loads(raw))
