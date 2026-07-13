"""Live Relay room and event wire contracts."""

from datetime import datetime

from pydantic import Field

from webwoven_api.http.contracts.common import ApiModel, EntityResponse
from webwoven_api.rooms.models import RoomState


class RoomCreateRequest(ApiModel):
    round_id: str | None = None


class RoomReadyRequest(ApiModel):
    ready: bool = True


class RoomParticipantResponse(ApiModel):
    guest_id: str
    display_name: str
    is_self: bool
    ready: bool
    connected: bool
    session_id: str | None
    moves: int
    hints_used: int
    progress_band: int = Field(ge=0, le=4)
    finish_rank: int | None


class RoomResponse(ApiModel):
    code: str
    state: RoomState
    is_host: bool
    graph_version: str
    round_id: str
    start: EntityResponse
    target: EntityResponse
    participants: list[RoomParticipantResponse]
    sequence: int
    countdown_ends_at: datetime | None
    grace_ends_at: datetime | None


class RoomEventResponse(ApiModel):
    sequence: int
    type: str
    occurred_at: datetime
    payload: dict[str, object]
