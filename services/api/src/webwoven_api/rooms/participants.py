"""Live Relay participant lookup and immutable replacement helpers."""

from webwoven_api.domain.errors import ForbiddenError
from webwoven_api.rooms.models import Participant, Room


def require_participant(room: Room, guest_id: str) -> Participant:
    participant = room.participant(guest_id)
    if participant is None:
        raise ForbiddenError("Join this lobby first")
    return participant


def require_active_participant(room: Room, guest_id: str) -> Participant:
    participant = require_participant(room, guest_id)
    if not participant.active:
        raise ForbiddenError("This player is no longer active in the lobby")
    return participant


def replace_participant(
    participants: tuple[Participant, ...], updated: Participant
) -> tuple[Participant, ...]:
    return tuple(updated if item.guest_id == updated.guest_id else item for item in participants)
