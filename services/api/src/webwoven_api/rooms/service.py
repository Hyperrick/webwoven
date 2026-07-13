"""Live Relay lifecycle, reconnect, and coarse-progress orchestration."""

import secrets
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from webwoven_api.domain.errors import DomainError, ForbiddenError, NotFoundError
from webwoven_api.graph.contracts import GraphReader, Round
from webwoven_api.guests.models import Guest
from webwoven_api.rooms.broker import RoomEventBroker
from webwoven_api.rooms.models import Participant, Room, RoomEvent, RoomState
from webwoven_api.rooms.repository import RoomRepository
from webwoven_api.sessions.models import GameSession, SessionMode, SessionStatus
from webwoven_api.sessions.service import SessionService

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


class RoomService:
    def __init__(
        self,
        *,
        graph: GraphReader,
        repository: RoomRepository,
        broker: RoomEventBroker,
        sessions: SessionService,
    ) -> None:
        self._graph = graph
        self._repository = repository
        self._broker = broker
        self._sessions = sessions

    async def create(self, guest: Guest, round_id: str | None = None) -> Room:
        round_ = self._select_round(round_id)
        for _ in range(20):
            code = "".join(secrets.choice(_CROCKFORD) for _ in range(6))
            now = datetime.now(UTC)
            room = Room(
                code=code,
                host_guest_id=guest.id,
                graph_version=self._graph.graph_version,
                round_id=round_.id,
                state=RoomState.LOBBY,
                participants=(Participant(guest.id, guest.display_name),),
                created_at=now,
                updated_at=now,
            )
            room, event = _append_event(room, "room.created", {"code": code})
            if await self._repository.create(room):
                await self._broker.publish(code, event)
                return room
        raise RuntimeError("Could not allocate a unique room code")

    async def get_for_guest(self, code: str, guest_id: str) -> Room:
        room = await self._get(code)
        if room.participant(guest_id) is None:
            raise ForbiddenError("Join this room before viewing it")
        return await self.tick(room)

    async def join(self, code: str, guest: Guest) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            existing = room.participant(guest.id)
            if existing is not None:
                participants = _replace_participant(
                    room.participants,
                    replace(existing, connected=True, display_name=guest.display_name),
                )
            else:
                if room.state is not RoomState.LOBBY:
                    raise DomainError("room_started", "This race has already started.")
                if len(room.participants) >= 4:
                    raise DomainError("room_full", "This room already has four players.")
                participants = (*room.participants, Participant(guest.id, guest.display_name))
            room = replace(room, participants=participants, updated_at=datetime.now(UTC))
            room, event = _append_event(
                room,
                "participant.joined",
                {"guest_id": guest.id, "display_name": guest.display_name},
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def set_ready(self, code: str, guest_id: str, ready: bool) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            if room.state is not RoomState.LOBBY:
                raise DomainError("room_started", "Readiness is locked after countdown begins.")
            participant = _require_participant(room, guest_id)
            participants = _replace_participant(
                room.participants, replace(participant, ready=ready)
            )
            room = replace(room, participants=participants, updated_at=datetime.now(UTC))
            room, event = _append_event(
                room, "participant.ready", {"guest_id": guest_id, "ready": ready}
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def start(self, code: str, guest_id: str) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            if room.host_guest_id != guest_id:
                raise ForbiddenError("Only the host can start the race")
            if room.state is not RoomState.LOBBY:
                raise DomainError("room_started", "This race has already started.")
            if len(room.participants) < 2:
                raise DomainError("not_enough_players", "Live Relay needs at least two players.")
            if not all(participant.ready for participant in room.participants):
                raise DomainError("players_not_ready", "Every player must be ready.")

            countdown_ends_at = datetime.now(UTC) + timedelta(seconds=3)
            participants: list[Participant] = []
            for participant in room.participants:
                session = await self._sessions.create(
                    guest_id=participant.guest_id,
                    mode=SessionMode.RELAY,
                    round_id=room.round_id,
                    room_code=room.code,
                    starts_at=countdown_ends_at,
                )
                participants.append(replace(participant, session_id=session.id))
            room = replace(
                room,
                state=RoomState.COUNTDOWN,
                participants=tuple(participants),
                countdown_ends_at=countdown_ends_at,
                updated_at=datetime.now(UTC),
            )
            room, event = _append_event(
                room,
                "race.countdown",
                {"countdown_ends_at": countdown_ends_at.isoformat()},
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def connect(
        self, code: str, guest_id: str, after: int
    ) -> tuple[Room, tuple[RoomEvent, ...]]:
        room = await self._set_connected(code, guest_id, True)
        retained = room.events
        if retained and after < retained[0].sequence - 1:
            return room, ()
        return room, tuple(event for event in retained if event.sequence > after)

    async def disconnect(self, code: str, guest_id: str) -> None:
        try:
            await self._set_connected(code, guest_id, False)
        except (NotFoundError, ForbiddenError):
            return

    async def sync_session(self, session: GameSession) -> Room | None:
        if session.room_code is None:
            return None
        code = session.room_code
        async with self._repository.lock(code):
            room = await self._get(code)
            participant = _require_participant(room, session.guest_id)
            distance = self._graph.distance_to_target(room.round_id, session.navigation.current_id)
            progress = _progress_band(distance, session.round.optimal_distance, session.status)
            finish_rank = participant.finish_rank
            finished_at = participant.finished_at
            state = room.state
            grace_ends_at = room.grace_ends_at
            if session.status is SessionStatus.COMPLETED and finished_at is None:
                finished_at = session.completed_at
                finish_rank = 1 + sum(other.finished_at is not None for other in room.participants)
                if state is RoomState.RACING:
                    state = RoomState.GRACE_PERIOD
                    grace_ends_at = datetime.now(UTC) + timedelta(seconds=30)
            updated = replace(
                participant,
                moves=session.navigation.moves,
                hints_used=len(session.hints),
                progress_band=progress,
                finished_at=finished_at,
                finish_rank=finish_rank,
            )
            participants = _replace_participant(room.participants, updated)
            if all(item.finished_at is not None for item in participants):
                state = RoomState.FINISHED
            room = replace(
                room,
                participants=participants,
                state=state,
                grace_ends_at=grace_ends_at,
                updated_at=datetime.now(UTC),
            )
            event_type = "race.finished" if finished_at is not None else "race.progress"
            room, event = _append_event(
                room,
                event_type,
                {
                    "guest_id": session.guest_id,
                    "moves": updated.moves,
                    "hints_used": updated.hints_used,
                    "progress_band": updated.progress_band,
                    "finish_rank": updated.finish_rank,
                },
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def tick(self, room: Room) -> Room:
        now = datetime.now(UTC)
        next_state: RoomState | None = None
        event_type: str | None = None
        if room.state is RoomState.COUNTDOWN and room.countdown_ends_at is not None:
            if now >= room.countdown_ends_at:
                next_state, event_type = RoomState.RACING, "race.started"
        elif (
            room.state is RoomState.GRACE_PERIOD
            and room.grace_ends_at is not None
            and now >= room.grace_ends_at
        ):
            next_state, event_type = RoomState.FINISHED, "race.finished"
        elif room.state is RoomState.FINISHED and now >= room.updated_at + timedelta(minutes=5):
            next_state, event_type = RoomState.CLOSED, "room.closed"
        if next_state is None or event_type is None:
            return room
        async with self._repository.lock(room.code):
            current = await self._get(room.code)
            if current.state is not room.state:
                return current
            current = replace(current, state=next_state, updated_at=now)
            current, event = _append_event(current, event_type, {"state": next_state.value})
            await self._repository.save(current)
        await self._broker.publish(room.code, event)
        return current

    async def _set_connected(self, code: str, guest_id: str, connected: bool) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            participant = _require_participant(room, guest_id)
            if participant.connected == connected:
                return room
            participants = _replace_participant(
                room.participants, replace(participant, connected=connected)
            )
            room = replace(room, participants=participants, updated_at=datetime.now(UTC))
            room, event = _append_event(
                room,
                "participant.connection",
                {"guest_id": guest_id, "connected": connected},
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def _get(self, code: str) -> Room:
        room = await self._repository.get(code.upper())
        if room is None:
            raise NotFoundError("Room not found")
        return room

    def _select_round(self, round_id: str | None) -> Round:
        if round_id is not None:
            round_ = self._graph.get_round(round_id)
            if round_ is None or not round_.published:
                raise NotFoundError("Published round not found")
            return round_
        rounds = self._graph.list_published_rounds()
        if not rounds:
            raise NotFoundError("No published rounds are available")
        return rounds[0]


def _append_event(
    room: Room, event_type: str, payload: dict[str, object]
) -> tuple[Room, RoomEvent]:
    event = RoomEvent(room.sequence + 1, event_type, datetime.now(UTC), payload)
    events = (*room.events[-199:], event)
    return replace(room, sequence=event.sequence, events=events), event


def _require_participant(room: Room, guest_id: str) -> Participant:
    participant = room.participant(guest_id)
    if participant is None:
        raise ForbiddenError("Join this room first")
    return participant


def _replace_participant(
    participants: tuple[Participant, ...], updated: Participant
) -> tuple[Participant, ...]:
    return tuple(updated if item.guest_id == updated.guest_id else item for item in participants)


def _progress_band(distance: int | None, optimal_distance: int, status: SessionStatus) -> int:
    if status is SessionStatus.COMPLETED:
        return 4
    if distance is None:
        return 0
    ratio = distance / max(optimal_distance, 1)
    if ratio <= 0.34:
        return 3
    if ratio <= 0.67:
        return 2
    if ratio < 1:
        return 1
    return 0
