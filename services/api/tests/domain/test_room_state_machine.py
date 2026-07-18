"""Pure Relay deadline and rematch membership rules."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from webwoven_api.rooms.models import Participant, Room, RoomState
from webwoven_api.rooms.state_machine import (
    close_for_insufficient_rematch,
    command_window_is_open,
    next_transition_at,
    open_rematch_vote,
)

NOW = datetime(2026, 7, 18, 12, tzinfo=UTC)


def test_command_window_uses_deadlines_not_only_persisted_state() -> None:
    countdown = _room(
        RoomState.COUNTDOWN,
        countdown_ends_at=NOW,
    )
    grace = _room(
        RoomState.GRACE_PERIOD,
        grace_ends_at=NOW,
    )

    assert command_window_is_open(countdown, NOW)
    assert command_window_is_open(grace, NOW - timedelta(microseconds=1))
    assert not command_window_is_open(grace, NOW)
    assert next_transition_at(countdown) == NOW
    assert next_transition_at(grace) == NOW


def test_finished_room_opens_thirty_second_vote_and_close_deactivates_everyone() -> None:
    room = open_rematch_vote(_room(RoomState.GRACE_PERIOD), NOW)
    voted = replace(
        room,
        participants=(
            Participant("guest-1", "Atlas", session_id="session-1", rematch_vote=True),
            Participant("guest-2", "Compass", session_id="session-2", rematch_vote=False),
        ),
    )

    closed = close_for_insufficient_rematch(voted, NOW + timedelta(seconds=5))

    assert room.state is RoomState.FINISHED
    assert room.rematch_ends_at == NOW + timedelta(seconds=30)
    assert closed.state is RoomState.CLOSED
    assert all(not participant.active for participant in closed.participants)
    assert [participant.session_id for participant in closed.participants] == [
        "session-1",
        "session-2",
    ]


def _room(
    state: RoomState,
    *,
    countdown_ends_at: datetime | None = None,
    grace_ends_at: datetime | None = None,
) -> Room:
    return Room(
        code="ABC123",
        host_guest_id="guest-1",
        graph_version="graph-v1",
        round_id="round-1",
        state=state,
        participants=(Participant("guest-1", "Atlas"),),
        created_at=NOW,
        updated_at=NOW,
        countdown_ends_at=countdown_ends_at,
        grace_ends_at=grace_ends_at,
    )
