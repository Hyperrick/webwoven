"""Live Relay room, participant, and ordered event state."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RoomState(StrEnum):
    LOBBY = "lobby"
    COUNTDOWN = "countdown"
    RACING = "racing"
    GRACE_PERIOD = "grace_period"
    FINISHED = "finished"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class Participant:
    guest_id: str
    display_name: str
    ready: bool = False
    connected: bool = True
    session_id: str | None = None
    moves: int = 0
    hints_used: int = 0
    progress_band: int = 0
    finished_at: datetime | None = None
    finish_rank: int | None = None


@dataclass(frozen=True, slots=True)
class RoomEvent:
    sequence: int
    type: str
    occurred_at: datetime
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class Room:
    code: str
    host_guest_id: str
    graph_version: str
    round_id: str
    state: RoomState
    participants: tuple[Participant, ...]
    created_at: datetime
    updated_at: datetime
    sequence: int = 0
    events: tuple[RoomEvent, ...] = ()
    countdown_ends_at: datetime | None = None
    grace_ends_at: datetime | None = None

    def participant(self, guest_id: str) -> Participant | None:
        return next(
            (participant for participant in self.participants if participant.guest_id == guest_id),
            None,
        )
