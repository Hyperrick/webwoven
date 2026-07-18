"""Live Relay ownership of when player session moves are accepted."""

from datetime import UTC, datetime

from webwoven_api.domain.errors import DomainError, NotFoundError
from webwoven_api.rooms.repository import RoomRepository
from webwoven_api.rooms.state_machine import command_window_is_open
from webwoven_api.sessions.models import GameSession


class RelayCommandAuthorizer:
    def __init__(self, rooms: RoomRepository) -> None:
        self._rooms = rooms

    async def authorize(self, session: GameSession) -> None:
        if session.room_code is None:
            return
        room = await self._rooms.get(session.room_code)
        if room is None:
            raise NotFoundError("Lobby not found")
        participant = room.participant(session.guest_id)
        current_session = (
            participant is not None and participant.active and participant.session_id == session.id
        )
        if not current_session or not command_window_is_open(room, datetime.now(UTC)):
            raise DomainError(
                "race_not_active",
                "Moves are accepted only while the multiplayer race is active.",
            )
