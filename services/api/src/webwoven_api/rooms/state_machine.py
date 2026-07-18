"""Pure Live Relay timing and rematch membership rules."""

from dataclasses import replace
from datetime import datetime, timedelta

from webwoven_api.rooms.models import Participant, Room, RoomCloseReason, RoomState

REMATCH_WINDOW = timedelta(seconds=30)


def active_participants(room: Room) -> tuple[Participant, ...]:
    return tuple(participant for participant in room.participants if participant.active)


def command_window_is_open(room: Room, now: datetime) -> bool:
    if room.state is RoomState.RACING:
        return True
    if room.state is RoomState.COUNTDOWN:
        return room.countdown_ends_at is not None and now >= room.countdown_ends_at
    if room.state is RoomState.GRACE_PERIOD:
        return room.grace_ends_at is not None and now < room.grace_ends_at
    return False


def next_transition_at(room: Room) -> datetime | None:
    if room.state is RoomState.COUNTDOWN:
        return room.countdown_ends_at
    if room.state is RoomState.GRACE_PERIOD:
        return room.grace_ends_at
    if room.state is RoomState.FINISHED:
        return room.rematch_ends_at
    return None


def open_rematch_vote(room: Room, now: datetime) -> Room:
    return replace(
        room,
        state=RoomState.FINISHED,
        countdown_ends_at=None,
        grace_ends_at=None,
        rematch_ends_at=now + REMATCH_WINDOW,
        close_reason=None,
        participants=tuple(
            replace(participant, rematch_vote=None) for participant in room.participants
        ),
        updated_at=now,
    )


def rematch_vote_is_ready(room: Room, now: datetime) -> bool:
    if room.state is not RoomState.FINISHED:
        return False
    participants = active_participants(room)
    deadline_passed = room.rematch_ends_at is not None and now >= room.rematch_ends_at
    all_voted = bool(participants) and all(
        participant.rematch_vote is not None for participant in participants
    )
    return deadline_passed or all_voted


def accepted_rematch_participants(room: Room) -> tuple[Participant, ...]:
    return tuple(
        participant for participant in active_participants(room) if participant.rematch_vote is True
    )


def close_for_insufficient_rematch(room: Room, now: datetime) -> Room:
    return replace(
        room,
        state=RoomState.CLOSED,
        countdown_ends_at=None,
        grace_ends_at=None,
        rematch_ends_at=None,
        close_reason=RoomCloseReason.NOT_ENOUGH_PLAYERS,
        participants=tuple(
            replace(
                participant,
                active=False,
                ready=False,
            )
            for participant in room.participants
        ),
        updated_at=now,
    )
