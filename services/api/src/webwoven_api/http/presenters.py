"""Map domain state into public API snapshots without enforcing game rules."""

from collections import defaultdict
from datetime import date

from webwoven_api.daily.models import DailyAssignment, DailyScore
from webwoven_api.domain.hints import HintResult
from webwoven_api.graph.contracts import Entity, GraphReader, Round
from webwoven_api.http.contracts.common import EntityResponse
from webwoven_api.http.contracts.daily import (
    DailyLeaderboardResponse,
    DailyResponse,
    LeaderboardEntry,
)
from webwoven_api.http.contracts.rooms import RoomParticipantResponse, RoomResponse
from webwoven_api.http.contracts.sessions import (
    EdgeTargetResponse,
    HintResponse,
    HintUseResponse,
    RelationGroupResponse,
    SessionSnapshot,
)
from webwoven_api.rooms.models import Room
from webwoven_api.sessions.models import GameSession
from webwoven_api.sessions.service import SessionService


class SessionPresenter:
    def __init__(self, graph: GraphReader, sessions: SessionService) -> None:
        self._graph = graph
        self._sessions = sessions

    def snapshot(self, session: GameSession) -> SessionSnapshot:
        start = self._entity(session.round.start_id)
        target = self._entity(session.round.target_id)
        current = self._entity(session.navigation.current_id)
        navigation = [self._entity(entity_id) for entity_id in session.navigation.stack]
        trail = [self._entity(entity_id) for entity_id in session.navigation.trail]
        grouped: defaultdict[tuple[str, str], list[EdgeTargetResponse]] = defaultdict(list)
        if session.status.value == "active":
            for edge in self._graph.get_edges(session.navigation.current_id):
                grouped[(edge.relation_key, edge.relation_label)].append(
                    EdgeTargetResponse(
                        edge_token=self._sessions.issue_edge_token(session, edge.id),
                        explanation=edge.explanation,
                        target=entity_response(edge.target),
                    )
                )
        relation_groups = [
            RelationGroupResponse(property_id=key, label=label, edges=edges)
            for (key, label), edges in sorted(grouped.items())
        ]
        hints = [
            HintUseResponse(
                hint_type=hint.hint_type,
                penalty=hint.penalty,
                relation_property_id=hint.relation_key,
                entity_qid=hint.entity_id,
                message=hint.message,
                used_at=hint.used_at,
            )
            for hint in session.hints
        ]
        return SessionSnapshot(
            id=session.id,
            mode=session.mode,
            status=session.status,
            graph_version=session.graph_version,
            round_id=session.round.id,
            category=session.round.category,
            difficulty=session.round.difficulty,
            start=start,
            target=target,
            current=current,
            navigation_stack=navigation,
            trail=trail,
            moves=session.navigation.moves,
            hints_used=hints,
            hint_penalty=session.hint_penalty,
            state_version=session.state_version,
            started_at=session.started_at,
            completed_at=session.completed_at,
            final_score=session.final_score,
            daily_day=session.daily_day,
            relation_groups=relation_groups,
        )

    @staticmethod
    def hint_response(hint: HintResult | None) -> HintResponse | None:
        if hint is None:
            return None
        return HintResponse(
            hint_type=hint.hint_type,
            penalty=hint.penalty,
            relation_property_id=hint.relation_key,
            entity_qid=hint.entity_id,
            message=hint.message,
        )

    def _entity(self, entity_id: str) -> EntityResponse:
        entity = self._graph.get_entity(entity_id)
        if entity is None:
            raise RuntimeError(f"Pinned graph entity is missing: {entity_id}")
        return entity_response(entity)


def entity_response(entity: Entity) -> EntityResponse:
    return EntityResponse(
        qid=entity.id,
        label=entity.label,
        description=entity.description,
        category=entity.category,
        entity_type=entity.entity_type,
        image_path=entity.image_path,
    )


def daily_response(assignment: DailyAssignment, round_: Round, graph: GraphReader) -> DailyResponse:
    start = graph.get_entity(round_.start_id)
    target = graph.get_entity(round_.target_id)
    if start is None or target is None:
        raise RuntimeError("Daily round references a missing entity")
    return DailyResponse(
        day=assignment.day,
        graph_version=assignment.graph_version,
        round_id=round_.id,
        category=round_.category,
        difficulty=round_.difficulty,
        optimal_distance=round_.optimal_distance,
        time_window=round_.time_window,
        start=entity_response(start),
        target=entity_response(target),
    )


def leaderboard_response(day: date, scores: tuple[DailyScore, ...]) -> DailyLeaderboardResponse:
    return DailyLeaderboardResponse(
        day=day,
        entries=[
            LeaderboardEntry(
                rank=index,
                display_name=score.display_name,
                score=score.score,
                moves=score.moves,
                hints_used=score.hints_used,
                elapsed_seconds=score.elapsed_seconds,
                completed_at=score.completed_at,
            )
            for index, score in enumerate(scores, start=1)
        ],
    )


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
