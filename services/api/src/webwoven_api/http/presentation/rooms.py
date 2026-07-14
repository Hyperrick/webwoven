"""Multiplayer-room wire presentation."""

from webwoven_api.graph.contracts import GraphReader
from webwoven_api.http.contracts.rooms import RoomParticipantResponse, RoomResponse
from webwoven_api.http.presentation.entities import entity_response
from webwoven_api.rooms.models import Room


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
        start=entity_response(start),
        target=entity_response(target),
        participants=[
            RoomParticipantResponse(
                guest_id=participant.guest_id,
                display_name=participant.display_name,
                is_self=participant.guest_id == guest_id,
                ready=participant.ready,
                connected=participant.connected,
                session_id=(participant.session_id if participant.guest_id == guest_id else None),
                moves=participant.moves,
                hints_used=participant.hints_used,
                progress_band=participant.progress_band,
                finish_rank=participant.finish_rank,
            )
            for participant in room.participants
        ],
        sequence=room.sequence,
        countdown_ends_at=room.countdown_ends_at,
        grace_ends_at=room.grace_ends_at,
    )
