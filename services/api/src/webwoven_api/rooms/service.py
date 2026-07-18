"""Live Relay lifecycle, reconnect, and coarse-progress orchestration."""

import secrets
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from webwoven_api.domain.errors import DomainError, ForbiddenError, NotFoundError
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import GraphReader, Round
from webwoven_api.guests.models import Guest
from webwoven_api.rooms.broker import RoomEventBroker
from webwoven_api.rooms.events import append_room_event
from webwoven_api.rooms.models import (
    Participant,
    Room,
    RoomCloseReason,
    RoomEvent,
    RoomState,
)
from webwoven_api.rooms.participants import (
    replace_participant,
    require_active_participant,
    require_participant,
)
from webwoven_api.rooms.progress import progress_band
from webwoven_api.rooms.repository import RoomRepository
from webwoven_api.rooms.state_machine import (
    accepted_rematch_participants,
    active_participants,
    close_for_insufficient_rematch,
    open_rematch_vote,
    rematch_vote_is_ready,
)
from webwoven_api.sessions.models import GameSession, SessionMode, SessionStatus
from webwoven_api.sessions.selection import RoundSelector
from webwoven_api.sessions.service import SessionService

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_GRACE_PERIOD = timedelta(seconds=30)


class RoomService:
    def __init__(
        self,
        *,
        graph: GraphReader,
        repository: RoomRepository,
        broker: RoomEventBroker,
        sessions: SessionService,
        round_selector: RoundSelector,
        start_delay_seconds: float = 5,
    ) -> None:
        self._graph = graph
        self._repository = repository
        self._broker = broker
        self._sessions = sessions
        self._round_selector = round_selector
        self._start_delay_seconds = start_delay_seconds

    async def create(
        self,
        guest: Guest,
        difficulty: Difficulty,
        category: str | None = None,
        round_id: str | None = None,
    ) -> Room:
        round_ = await self._select_round(guest.id, difficulty, category, round_id)
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
            room, event = append_room_event(room, "room.created", {"code": code}, now)
            if await self._repository.create(room):
                await self._broker.publish(code, event)
                return room
        raise RuntimeError("Could not allocate a unique room code")

    async def get_for_guest(self, code: str, guest_id: str) -> Room:
        room = await self._get(code)
        if room.participant(guest_id) is None:
            raise ForbiddenError("Join this lobby before viewing it")
        return await self.tick(room)

    async def get_for_invite(self, code: str) -> Room:
        return await self.tick(await self._get(code))

    async def join(self, code: str, guest: Guest) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            existing = room.participant(guest.id)
            if existing is not None:
                if not existing.active:
                    raise DomainError(
                        "room_membership_ended",
                        "This player's lobby membership has ended.",
                    )
                participants = replace_participant(
                    room.participants,
                    replace(existing, connected=True, display_name=guest.display_name),
                )
            else:
                if room.state is not RoomState.LOBBY:
                    raise DomainError("room_started", "This lobby's race has already started.")
                if len(active_participants(room)) >= 4:
                    raise DomainError("room_full", "This lobby already has four players.")
                participants = (*room.participants, Participant(guest.id, guest.display_name))
            now = datetime.now(UTC)
            room = replace(room, participants=participants, updated_at=now)
            room, event = append_room_event(
                room,
                "participant.joined",
                {"guest_id": guest.id, "display_name": guest.display_name},
                now,
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def set_ready(self, code: str, guest_id: str, ready: bool) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            if room.state is not RoomState.LOBBY:
                raise DomainError(
                    "room_started", "Lobby readiness is locked after countdown begins."
                )
            participant = require_active_participant(room, guest_id)
            participants = replace_participant(room.participants, replace(participant, ready=ready))
            now = datetime.now(UTC)
            room = replace(room, participants=participants, updated_at=now)
            room, event = append_room_event(
                room,
                "participant.ready",
                {"guest_id": guest_id, "ready": ready},
                now,
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def start(self, code: str, guest_id: str) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            if room.host_guest_id != guest_id:
                raise ForbiddenError("Only the lobby host can start the race")
            if room.state is not RoomState.LOBBY:
                raise DomainError("room_started", "This lobby's race has already started.")
            participants = active_participants(room)
            if len(participants) < 2:
                raise DomainError("not_enough_players", "Live Relay needs at least two players.")
            if not all(participant.ready for participant in participants):
                raise DomainError("players_not_ready", "Every player must be ready.")

            countdown_ends_at = datetime.now(UTC) + timedelta(seconds=self._start_delay_seconds)
            started: list[Participant] = []
            for participant in participants:
                session = await self._sessions.create(
                    guest_id=participant.guest_id,
                    mode=SessionMode.RELAY,
                    round_id=room.round_id,
                    room_code=room.code,
                    starts_at=countdown_ends_at,
                )
                started.append(replace(participant, session_id=session.id))
            room = replace(
                room,
                state=RoomState.COUNTDOWN,
                participants=tuple(started),
                countdown_ends_at=countdown_ends_at,
                grace_ends_at=None,
                rematch_ends_at=None,
                close_reason=None,
                updated_at=datetime.now(UTC),
            )
            room, event = append_room_event(
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
        room = await self.tick(await self._set_connected(code, guest_id, True))
        retained = room.events
        if retained and after < retained[0].sequence - 1:
            return room, ()
        return room, tuple(event for event in retained if event.sequence > after)

    async def disconnect(self, code: str, guest_id: str) -> None:
        try:
            await self._set_connected(code, guest_id, False)
        except (NotFoundError, ForbiddenError):
            return

    async def vote_rematch(self, code: str, guest_id: str, accept: bool) -> Room:
        events: tuple[RoomEvent, ...] = ()
        rejected = False
        async with self._repository.lock(code):
            room = await self._get(code)
            now = datetime.now(UTC)
            if room.state is not RoomState.FINISHED:
                raise DomainError("rematch_not_open", "This rematch vote is not open.")
            if room.rematch_ends_at is None or now >= room.rematch_ends_at:
                room, events, _, _ = await self._advance_locked(room, now)
                if events:
                    await self._repository.save(room)
                rejected = True
            else:
                participant = require_active_participant(room, guest_id)
                if participant.rematch_vote is accept:
                    return room
                participant = replace(participant, rematch_vote=accept)
                room = replace(
                    room,
                    participants=replace_participant(room.participants, participant),
                    updated_at=now,
                )
                room, vote_event = append_room_event(
                    room,
                    "participant.rematch_vote",
                    {"guest_id": guest_id, "accept": accept},
                    now,
                )
                event_list = [vote_event]
                if rematch_vote_is_ready(room, now):
                    room, resolution = await self._resolve_rematch_locked(room, now)
                    event_list.append(resolution)
                events = tuple(event_list)
                await self._repository.save(room)
        await self._publish(code, events)
        if rejected:
            raise DomainError("rematch_closed", "The rematch vote has ended.")
        return room

    async def sync_session(self, session: GameSession) -> Room | None:
        if session.room_code is None:
            return None
        code = session.room_code
        events: list[RoomEvent] = []
        async with self._repository.lock(code):
            room = await self._get(code)
            participant = require_active_participant(room, session.guest_id)
            if participant.session_id != session.id:
                raise DomainError("race_not_active", "This Relay session is no longer current.")
            now = datetime.now(UTC)
            if (
                room.state is RoomState.COUNTDOWN
                and room.countdown_ends_at is not None
                and now >= room.countdown_ends_at
            ):
                room = replace(room, state=RoomState.RACING, updated_at=now)
                room, started_event = append_room_event(
                    room, "race.started", {"state": RoomState.RACING.value}, now
                )
                events.append(started_event)

            distance = self._graph.distance_to_target(room.round_id, session.navigation.current_id)
            progress = progress_band(distance, session.round.optimal_distance, session.status)
            newly_finished = (
                session.status is SessionStatus.COMPLETED and participant.finished_at is None
            )
            finish_rank = participant.finish_rank
            finished_at = participant.finished_at
            if newly_finished:
                finished_at = session.completed_at
                finish_rank = 1 + sum(
                    other.active and other.finished_at is not None for other in room.participants
                )
            updated = replace(
                participant,
                moves=session.navigation.moves,
                hints_used=len(session.hints),
                progress_band=progress,
                finished_at=finished_at,
                finish_rank=finish_rank,
            )
            room = replace(
                room,
                participants=replace_participant(room.participants, updated),
                updated_at=now,
            )
            if newly_finished and room.state is RoomState.RACING:
                room = replace(
                    room,
                    state=RoomState.GRACE_PERIOD,
                    grace_ends_at=now + _GRACE_PERIOD,
                )
            all_finished = all(item.finished_at is not None for item in active_participants(room))
            if newly_finished and all_finished:
                room = open_rematch_vote(room, now)

            event_type = (
                "race.finished"
                if newly_finished and room.state is RoomState.FINISHED
                else "participant.finished"
                if newly_finished
                else "race.progress"
            )
            payload: dict[str, object] = {
                "guest_id": session.guest_id,
                "moves": updated.moves,
                "hints_used": updated.hints_used,
                "progress_band": updated.progress_band,
                "finish_rank": updated.finish_rank,
            }
            if room.grace_ends_at is not None:
                payload["grace_ends_at"] = room.grace_ends_at.isoformat()
            if room.rematch_ends_at is not None:
                payload["rematch_ends_at"] = room.rematch_ends_at.isoformat()
            room, progress_event = append_room_event(room, event_type, payload, now)
            events.append(progress_event)
            await self._repository.save(room)
        await self._publish(code, tuple(events))
        return room

    async def tick(self, room: Room) -> Room:
        events: tuple[RoomEvent, ...] = ()
        expired_session_ids: tuple[str, ...] = ()
        expired_at: datetime | None = None
        async with self._repository.lock(room.code):
            current = await self._get(room.code)
            current, events, expired_session_ids, expired_at = await self._advance_locked(
                current, datetime.now(UTC)
            )
            if events:
                await self._repository.save(current)
        if expired_at is not None:
            for session_id in expired_session_ids:
                await self._sessions.expire_relay(session_id, expired_at)
        await self._publish(room.code, events)
        return current

    async def _advance_locked(
        self, room: Room, now: datetime
    ) -> tuple[Room, tuple[RoomEvent, ...], tuple[str, ...], datetime | None]:
        if (
            room.state is RoomState.COUNTDOWN
            and room.countdown_ends_at is not None
            and now >= room.countdown_ends_at
        ):
            room = replace(room, state=RoomState.RACING, updated_at=now)
            room, event = append_room_event(
                room, "race.started", {"state": RoomState.RACING.value}, now
            )
            return room, (event,), (), None
        if (
            room.state is RoomState.GRACE_PERIOD
            and room.grace_ends_at is not None
            and now >= room.grace_ends_at
        ):
            expired_at = room.grace_ends_at
            expired = tuple(
                participant.session_id
                for participant in active_participants(room)
                if participant.finished_at is None and participant.session_id is not None
            )
            room = open_rematch_vote(room, now)
            room, event = append_room_event(
                room,
                "race.finished",
                {
                    "state": RoomState.FINISHED.value,
                    "rematch_ends_at": room.rematch_ends_at.isoformat()
                    if room.rematch_ends_at is not None
                    else None,
                },
                now,
            )
            return room, (event,), expired, expired_at
        if room.state is RoomState.FINISHED and rematch_vote_is_ready(room, now):
            room, event = await self._resolve_rematch_locked(room, now)
            return room, (event,), (), None
        return room, (), (), None

    async def _resolve_rematch_locked(self, room: Room, now: datetime) -> tuple[Room, RoomEvent]:
        accepted = accepted_rematch_participants(room)
        if len(accepted) < 2:
            room = close_for_insufficient_rematch(room, now)
            return append_room_event(
                room,
                "room.closed",
                {
                    "state": room.state.value,
                    "reason": RoomCloseReason.NOT_ENOUGH_PLAYERS.value,
                },
                now,
            )

        accepted_ids = {participant.guest_id for participant in accepted}
        host_guest_id = (
            room.host_guest_id if room.host_guest_id in accepted_ids else accepted[0].guest_id
        )
        previous_round = self._graph.get_round(room.round_id)
        if previous_round is None:
            raise RuntimeError("Room references a missing round")
        next_round = await self._round_selector.select(
            guest_id=host_guest_id,
            category=previous_round.category,
            difficulty=previous_round.difficulty,
            source="relay",
        )
        countdown_ends_at = now + timedelta(seconds=self._start_delay_seconds)
        participants: list[Participant] = []
        for participant in room.participants:
            if participant.guest_id not in accepted_ids:
                participants.append(replace(participant, active=False, ready=False))
                continue
            session = await self._sessions.create(
                guest_id=participant.guest_id,
                mode=SessionMode.RELAY,
                round_id=next_round.id,
                room_code=room.code,
                starts_at=countdown_ends_at,
            )
            participants.append(
                replace(
                    participant,
                    active=True,
                    ready=True,
                    session_id=session.id,
                    moves=0,
                    hints_used=0,
                    progress_band=0,
                    finished_at=None,
                    finish_rank=None,
                    rematch_vote=None,
                )
            )
        room = replace(
            room,
            host_guest_id=host_guest_id,
            round_id=next_round.id,
            state=RoomState.COUNTDOWN,
            participants=tuple(participants),
            countdown_ends_at=countdown_ends_at,
            grace_ends_at=None,
            rematch_ends_at=None,
            close_reason=None,
            updated_at=now,
        )
        return append_room_event(
            room,
            "race.countdown",
            {
                "countdown_ends_at": countdown_ends_at.isoformat(),
                "round_id": next_round.id,
                "rematch": True,
            },
            now,
        )

    async def _set_connected(self, code: str, guest_id: str, connected: bool) -> Room:
        async with self._repository.lock(code):
            room = await self._get(code)
            participant = require_participant(room, guest_id)
            if participant.connected == connected:
                return room
            participants = replace_participant(
                room.participants, replace(participant, connected=connected)
            )
            now = datetime.now(UTC)
            room = replace(room, participants=participants, updated_at=now)
            room, event = append_room_event(
                room,
                "participant.connection",
                {"guest_id": guest_id, "connected": connected},
                now,
            )
            await self._repository.save(room)
        await self._broker.publish(code, event)
        return room

    async def _publish(self, code: str, events: tuple[RoomEvent, ...]) -> None:
        for event in events:
            await self._broker.publish(code, event)

    async def _get(self, code: str) -> Room:
        room = await self._repository.get(code.upper())
        if room is None:
            raise NotFoundError("Lobby not found")
        return room

    async def _select_round(
        self,
        guest_id: str,
        difficulty: Difficulty,
        category: str | None,
        round_id: str | None,
    ) -> Round:
        if round_id is not None:
            round_ = self._graph.get_round(round_id)
            if round_ is None or not round_.published:
                raise NotFoundError("Published round not found")
            return round_
        return await self._round_selector.select(
            guest_id=guest_id,
            category=category,
            difficulty=difficulty,
            source="relay",
        )
