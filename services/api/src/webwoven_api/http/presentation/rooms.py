"""Multiplayer-room wire presentation."""

from webwoven_api.graph.contracts import GraphReader
from webwoven_api.http.contracts.rooms import (
    RoomInviteResponse,
    RoomParticipantResponse,
    RoomResponse,
)
from webwoven_api.http.presentation.entities import entity_response
from webwoven_api.rooms.models import Room, RoomState
from webwoven_api.rooms.state_machine import active_participants


def room_response(room: Room, guest_id: str, graph: GraphReader) -> RoomResponse:
    round_ = graph.get_round(room.round_id)
    if round_ is None:
        raise RuntimeError("Room references a missing round")
    start = graph.get_entity(round_.start_id)
    target = graph.get_entity(round_.target_id)
    if start is None or target is None:
        raise RuntimeError("Room round references a missing entity")
    return RoomResponse(
        code=room.code,
        state=room.state,
        is_host=room.host_guest_id == guest_id,
        graph_version=room.graph_version,
        round_id=room.round_id,
        category=round_.category,
        difficulty=round_.difficulty,
        start=entity_response(start),
        target=entity_response(target),
        participants=[
            RoomParticipantResponse(
                guest_id=participant.guest_id,
                display_name=participant.display_name,
                is_self=participant.guest_id == guest_id,
                active=participant.active,
                ready=participant.ready,
                connected=participant.connected,
                session_id=(participant.session_id if participant.guest_id == guest_id else None),
                moves=participant.moves,
                hints_used=participant.hints_used,
                progress_band=participant.progress_band,
                finish_rank=participant.finish_rank,
                rematch_vote=participant.rematch_vote,
            )
            for participant in room.participants
        ],
        sequence=room.sequence,
        countdown_ends_at=room.countdown_ends_at,
        grace_ends_at=room.grace_ends_at,
        rematch_ends_at=room.rematch_ends_at,
        close_reason=room.close_reason,
    )


def room_invite_response(room: Room, guest_id: str) -> RoomInviteResponse:
    host = room.participant(room.host_guest_id)
    if host is None:
        raise RuntimeError("Room host is missing from its participants")
    player_count = len(active_participants(room))
    participant = room.participant(guest_id)
    is_member = participant is not None and participant.active
    return RoomInviteResponse(
        code=room.code,
        host_display_name=host.display_name,
        state=room.state,
        player_count=player_count,
        is_member=is_member,
        joinable=is_member or (room.state is RoomState.LOBBY and player_count < 4),
    )
