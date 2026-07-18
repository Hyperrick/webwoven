"""Ordered event append operation for Live Relay rooms."""

from dataclasses import replace
from datetime import UTC, datetime

from webwoven_api.rooms.models import Room, RoomEvent


def append_room_event(
    room: Room,
    event_type: str,
    payload: dict[str, object],
    occurred_at: datetime | None = None,
) -> tuple[Room, RoomEvent]:
    event = RoomEvent(
        room.sequence + 1,
        event_type,
        occurred_at or datetime.now(UTC),
        payload,
    )
    events = (*room.events[-199:], event)
    return replace(room, sequence=event.sequence, events=events), event
