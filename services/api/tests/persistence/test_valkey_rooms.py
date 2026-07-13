"""Valkey room behavior against an external-service-free fake client."""

from datetime import UTC, datetime

from webwoven_api.persistence.valkey.rooms import ValkeyRoomRepository
from webwoven_api.rooms.models import Participant, Room, RoomState


class FakeValkey:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int,
        only_if_absent: bool = False,
    ) -> bool:
        del ttl_seconds
        if only_if_absent and key in self.values:
            return False
        self.values[key] = value
        return True

    async def compare_delete(self, key: str, expected: str) -> bool:
        if self.values.get(key) != expected:
            return False
        del self.values[key]
        return True

    async def compare_expire(self, key: str, expected: str, ttl_seconds: int) -> bool:
        del ttl_seconds
        return self.values.get(key) == expected


class FakeArchive:
    def __init__(self) -> None:
        self.rooms: list[Room] = []

    async def archive(self, room: Room) -> None:
        self.rooms.append(room)


async def test_room_creation_is_atomic_and_session_index_reconnects() -> None:
    valkey = FakeValkey()
    archive = FakeArchive()
    repository = ValkeyRoomRepository(
        valkey,  # type: ignore[arg-type]
        archive,
        active_ttl_seconds=3600,
        completed_ttl_seconds=600,
        lock_lease_seconds=30,
        lock_wait_seconds=1,
    )
    room = _room(RoomState.RACING)
    assert await repository.create(room)
    assert not await repository.create(room)

    await repository.save(room)
    assert await repository.get("abc123") == room
    assert await repository.find_by_session("session-1") == room
    assert archive.rooms == []


async def test_finished_room_is_archived_but_kept_briefly_for_results() -> None:
    valkey = FakeValkey()
    archive = FakeArchive()
    repository = ValkeyRoomRepository(
        valkey,  # type: ignore[arg-type]
        archive,
        active_ttl_seconds=3600,
        completed_ttl_seconds=600,
        lock_lease_seconds=30,
        lock_wait_seconds=1,
    )
    room = _room(RoomState.FINISHED)
    await repository.save(room)
    assert archive.rooms == [room]
    assert await repository.get(room.code) == room


def _room(state: RoomState) -> Room:
    now = datetime(2026, 7, 13, tzinfo=UTC)
    return Room(
        code="ABC123",
        host_guest_id="guest-1",
        graph_version="graph-v1",
        round_id="round-1",
        state=state,
        participants=(Participant("guest-1", "Atlas", session_id="session-1"),),
        created_at=now,
        updated_at=now,
    )
