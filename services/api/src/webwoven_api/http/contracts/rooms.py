"""Live Relay room and event wire contracts."""

from datetime import datetime

from pydantic import Field

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.http.contracts.common import ApiModel, EntityResponse
from webwoven_api.rooms.models import RoomCloseReason, RoomState


class RoomCreateRequest(ApiModel):
    difficulty: Difficulty
    category: str | None = None
    round_id: str | None = None


class RoomReadyRequest(ApiModel):
    ready: bool = True


class RoomRematchRequest(ApiModel):
    accept: bool


class RoomParticipantResponse(ApiModel):
    guest_id: str
    display_name: str
    is_self: bool
    active: bool
    ready: bool
    connected: bool
    session_id: str | None
    moves: int
    hints_used: int
    progress_band: int = Field(ge=0, le=4)
    finish_rank: int | None
    rematch_vote: bool | None


class RoomResponse(ApiModel):
    code: str
    state: RoomState
    is_host: bool
    graph_version: str
    round_id: str
    category: str
    difficulty: Difficulty
    start: EntityResponse
    target: EntityResponse
    participants: list[RoomParticipantResponse]
    sequence: int
    countdown_ends_at: datetime | None
    grace_ends_at: datetime | None
    rematch_ends_at: datetime | None
    close_reason: RoomCloseReason | None


class RoomInviteResponse(ApiModel):
    code: str
    host_display_name: str
    state: RoomState
    player_count: int = Field(ge=0, le=4)
    max_players: int = Field(default=4, ge=4, le=4)
    is_member: bool
    joinable: bool


class RoomEventResponse(ApiModel):
    sequence: int
    type: str
    occurred_at: datetime
    payload: dict[str, object]
