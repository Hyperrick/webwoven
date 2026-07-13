"""Live Relay ownership of when player session moves are accepted."""

from webwoven_api.domain.errors import DomainError, NotFoundError
from webwoven_api.rooms.models import RoomState
from webwoven_api.rooms.repository import RoomRepository
from webwoven_api.sessions.models import GameSession


class RelayCommandAuthorizer:
    def __init__(self, rooms: RoomRepository) -> None:
        self._rooms = rooms

    async def authorize(self, session: GameSession) -> None:
        if session.room_code is None:
            return
        room = await self._rooms.get(session.room_code)
        if room is None:
            raise NotFoundError("Relay room not found")
        if room.state not in {RoomState.RACING, RoomState.GRACE_PERIOD}:
            raise DomainError(
                "race_not_active",
                "Moves are accepted only while the relay race is active.",
            )
