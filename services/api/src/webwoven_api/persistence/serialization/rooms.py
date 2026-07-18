"""Versioned JSON mapping for active Live Relay state and events."""

from datetime import datetime

from webwoven_api.persistence.serialization.values import (
    optional_datetime,
    optional_int,
    optional_string,
    require_bool,
    require_datetime,
    require_int,
    require_json_object,
    require_list,
    require_object,
    require_string,
)
from webwoven_api.rooms.models import (
    Participant,
    Room,
    RoomCloseReason,
    RoomEvent,
    RoomState,
)

_SCHEMA_VERSION = 2


def room_to_dict(room: Room) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "code": room.code,
        "host_guest_id": room.host_guest_id,
        "graph_version": room.graph_version,
        "round_id": room.round_id,
        "state": room.state.value,
        "participants": [_participant_to_dict(item) for item in room.participants],
        "created_at": room.created_at.isoformat(),
        "updated_at": room.updated_at.isoformat(),
        "sequence": room.sequence,
        "events": [room_event_to_dict(event) for event in room.events],
        "countdown_ends_at": _optional_datetime_value(room.countdown_ends_at),
        "grace_ends_at": _optional_datetime_value(room.grace_ends_at),
        "rematch_ends_at": _optional_datetime_value(room.rematch_ends_at),
        "close_reason": room.close_reason.value if room.close_reason is not None else None,
    }


def room_from_dict(value: object) -> Room:
    data = require_object(value, "room")
    version = require_int(data.get("schema_version"), "room.schema_version")
    if version not in {1, _SCHEMA_VERSION}:
        raise ValueError(f"Unsupported room persistence schema version: {version}")
    updated_at = require_datetime(data.get("updated_at"), "room.updated_at")
    return Room(
        code=require_string(data.get("code"), "room.code"),
        host_guest_id=require_string(data.get("host_guest_id"), "room.host_guest_id"),
        graph_version=require_string(data.get("graph_version"), "room.graph_version"),
        round_id=require_string(data.get("round_id"), "room.round_id"),
        state=RoomState(require_string(data.get("state"), "room.state")),
        participants=tuple(
            _participant_from_dict(item, version=version)
            for item in require_list(data.get("participants"), "room.participants")
        ),
        created_at=require_datetime(data.get("created_at"), "room.created_at"),
        updated_at=updated_at,
        sequence=require_int(data.get("sequence"), "room.sequence"),
        events=tuple(
            room_event_from_dict(item) for item in require_list(data.get("events"), "room.events")
        ),
        countdown_ends_at=optional_datetime(
            data.get("countdown_ends_at"), "room.countdown_ends_at"
        ),
        grace_ends_at=optional_datetime(data.get("grace_ends_at"), "room.grace_ends_at"),
        rematch_ends_at=(
            optional_datetime(data.get("rematch_ends_at"), "room.rematch_ends_at")
            if version >= 2
            else None
        ),
        close_reason=(_optional_close_reason(data.get("close_reason")) if version >= 2 else None),
    )


def room_event_to_dict(event: RoomEvent) -> dict[str, object]:
    return {
        "sequence": event.sequence,
        "type": event.type,
        "occurred_at": event.occurred_at.isoformat(),
        "payload": event.payload,
    }


def room_event_from_dict(value: object) -> RoomEvent:
    data = require_object(value, "room_event")
    return RoomEvent(
        sequence=require_int(data.get("sequence"), "room_event.sequence"),
        type=require_string(data.get("type"), "room_event.type"),
        occurred_at=require_datetime(data.get("occurred_at"), "room_event.occurred_at"),
        payload=require_json_object(data.get("payload"), "room_event.payload"),
    )


def _participant_to_dict(participant: Participant) -> dict[str, object]:
    return {
        "guest_id": participant.guest_id,
        "display_name": participant.display_name,
        "active": participant.active,
        "ready": participant.ready,
        "connected": participant.connected,
        "session_id": participant.session_id,
        "moves": participant.moves,
        "hints_used": participant.hints_used,
        "progress_band": participant.progress_band,
        "finished_at": _optional_datetime_value(participant.finished_at),
        "finish_rank": participant.finish_rank,
        "rematch_vote": participant.rematch_vote,
    }


def _participant_from_dict(value: object, *, version: int) -> Participant:
    data = require_object(value, "room.participants[]")
    return Participant(
        guest_id=require_string(data.get("guest_id"), "participant.guest_id"),
        display_name=require_string(data.get("display_name"), "participant.display_name"),
        active=(require_bool(data.get("active"), "participant.active") if version >= 2 else True),
        ready=require_bool(data.get("ready"), "participant.ready"),
        connected=require_bool(data.get("connected"), "participant.connected"),
        session_id=optional_string(data.get("session_id"), "participant.session_id"),
        moves=require_int(data.get("moves"), "participant.moves"),
        hints_used=require_int(data.get("hints_used"), "participant.hints_used"),
        progress_band=require_int(data.get("progress_band"), "participant.progress_band"),
        finished_at=optional_datetime(data.get("finished_at"), "participant.finished_at"),
        finish_rank=optional_int(data.get("finish_rank"), "participant.finish_rank"),
        rematch_vote=(
            _optional_bool(data.get("rematch_vote"), "participant.rematch_vote")
            if version >= 2
            else None
        ),
    )


def _optional_datetime_value(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _optional_bool(value: object, field: str) -> bool | None:
    if value is None:
        return None
    return require_bool(value, field)


def _optional_close_reason(value: object) -> RoomCloseReason | None:
    raw = optional_string(value, "room.close_reason")
    return RoomCloseReason(raw) if raw is not None else None
