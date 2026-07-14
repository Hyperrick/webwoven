"""Versioned, server-authoritative Route Race command orchestration."""

from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import uuid4

from webwoven_api.daily.service import DailyService
from webwoven_api.domain.errors import (
    DomainError,
    ForbiddenError,
    NotFoundError,
    StaleStateError,
)
from webwoven_api.domain.hints import HintCandidate, HintResult, select_hint
from webwoven_api.domain.navigation import follow_edge, go_back, start_navigation
from webwoven_api.domain.scoring import Difficulty, calculate_score
from webwoven_api.graph.contracts import GraphReader, Round
from webwoven_api.security.tokens import EdgeTokenSigner
from webwoven_api.sessions.authorization import SessionCommandAuthorizer
from webwoven_api.sessions.completion import SessionCompletionRecorder
from webwoven_api.sessions.exploration import backed_frame, followed_frame
from webwoven_api.sessions.frontier import playable_edges_for
from webwoven_api.sessions.models import (
    BackCommand,
    CommandExecution,
    FollowEdgeCommand,
    GameSession,
    HintUse,
    SessionCommand,
    SessionMode,
    SessionStatus,
    UseHintCommand,
)
from webwoven_api.sessions.repository import SessionRepository


class SessionService:
    def __init__(
        self,
        *,
        graph: GraphReader,
        repository: SessionRepository,
        daily: DailyService,
        edge_tokens: EdgeTokenSigner,
        completion_recorder: SessionCompletionRecorder,
        command_authorizer: SessionCommandAuthorizer,
    ) -> None:
        self._graph = graph
        self._repository = repository
        self._daily = daily
        self._edge_tokens = edge_tokens
        self._completion_recorder = completion_recorder
        self._command_authorizer = command_authorizer

    async def create(
        self,
        *,
        guest_id: str,
        mode: SessionMode,
        round_id: str | None = None,
        category: str | None = None,
        difficulty: Difficulty | None = None,
        room_code: str | None = None,
        starts_at: datetime | None = None,
    ) -> GameSession:
        round_, daily_day = await self._select_round(mode, round_id, category, difficulty)
        session = GameSession(
            id=str(uuid4()),
            guest_id=guest_id,
            mode=mode,
            graph_version=self._graph.graph_version,
            round=round_,
            navigation=start_navigation(round_.start_id),
            status=SessionStatus.ACTIVE,
            state_version=0,
            started_at=starts_at or datetime.now(UTC),
            room_code=room_code,
            daily_day=daily_day,
        )
        await self._repository.create(session)
        return session

    async def get_for_guest(self, session_id: str, guest_id: str) -> GameSession:
        session = await self._repository.get(session_id)
        if session is None:
            raise NotFoundError("Session not found")
        if session.guest_id != guest_id:
            raise ForbiddenError("This session belongs to another guest")
        return session

    async def execute(
        self,
        *,
        session_id: str,
        guest_id: str,
        command: SessionCommand,
    ) -> CommandExecution:
        async with self._repository.lock(session_id):
            session = await self.get_for_guest(session_id, guest_id)
            previous = await self._repository.get_command(session_id, command.command_id)
            if previous is not None:
                return replace(previous, duplicate=True)

            if session.status is not SessionStatus.ACTIVE:
                raise DomainError("session_not_active", "This route is no longer active.")
            await self._command_authorizer.authorize(session)
            if command.expected_state_version != session.state_version:
                raise StaleStateError(session.state_version)

            updated, hint = self._apply_command(session, command)
            updated, newly_completed, elapsed = self._finish_if_target(updated)
            result = CommandExecution(session=updated, applied=True, hint=hint)
            await self._repository.save(updated)
            await self._repository.save_command(session_id, command.command_id, result)
            if newly_completed:
                await self._completion_recorder.record_completion(updated, elapsed)
            return result

    def issue_edge_token(self, session: GameSession, edge_id: str) -> str:
        return self._edge_tokens.issue(
            session_id=session.id,
            graph_version=session.graph_version,
            source_id=session.navigation.current_id,
            edge_id=edge_id,
            state_version=session.state_version,
        )

    def _apply_command(
        self, session: GameSession, command: SessionCommand
    ) -> tuple[GameSession, HintResult | None]:
        if isinstance(command, FollowEdgeCommand):
            return self._follow(session, command), None
        if isinstance(command, BackCommand):
            return self._back(session), None
        return self._use_hint(session, command)

    def _back(self, session: GameSession) -> GameSession:
        source_id = session.navigation.current_id
        visible_edge_ids = tuple(
            edge.id for edge in playable_edges_for(self._graph, session.round, session.navigation)
        )
        navigation = go_back(session.navigation)
        decision = backed_frame(
            source_id=source_id,
            destination_id=navigation.current_id,
            visible_edge_ids=visible_edge_ids,
        )
        return replace(
            session,
            navigation=navigation,
            decision_history=(*session.decision_history, decision),
            state_version=session.state_version + 1,
        )

    def _follow(self, session: GameSession, command: FollowEdgeCommand) -> GameSession:
        claims = self._edge_tokens.verify(command.edge_token)
        expected = (
            claims.session_id == session.id
            and claims.graph_version == session.graph_version
            and claims.source_id == session.navigation.current_id
            and claims.state_version == session.state_version
        )
        if not expected:
            raise ForbiddenError("Edge token is not valid for this session state")
        edge = self._graph.get_edge(claims.edge_id)
        if edge is None:
            raise DomainError("edge_missing", "That relationship is unavailable.")
        visible_edge_ids = tuple(
            visible.id
            for visible in playable_edges_for(self._graph, session.round, session.navigation)
        )
        if edge.id not in visible_edge_ids:
            raise ForbiddenError("Edge token is not valid for the visible frontier")
        navigation = follow_edge(
            session.navigation,
            edge_source_id=edge.source_id,
            edge_target_id=edge.target_id,
        )
        decision = followed_frame(
            source_id=edge.source_id,
            destination_id=edge.target_id,
            visible_edge_ids=visible_edge_ids,
            selected_edge_id=edge.id,
        )
        return replace(
            session,
            navigation=navigation,
            decision_history=(*session.decision_history, decision),
            state_version=session.state_version + 1,
        )

    def _use_hint(
        self, session: GameSession, command: UseHintCommand
    ) -> tuple[GameSession, HintResult]:
        edges = playable_edges_for(self._graph, session.round, session.navigation)
        candidates = (
            HintCandidate(
                relation_key=edge.relation_key,
                entity_id=edge.target_id,
                entity_label=edge.target.label,
                distance=self._graph.distance_to_target(session.round.id, edge.target_id),
            )
            for edge in edges
        )
        hint = select_hint(
            command.hint_type,
            candidates,
            selected_relation_key=command.relation_key,
        )
        use = HintUse(
            hint_type=hint.hint_type,
            penalty=hint.penalty,
            relation_key=hint.relation_key,
            entity_id=hint.entity_id,
            message=hint.message,
            used_at=datetime.now(UTC),
        )
        updated = replace(
            session,
            hints=(*session.hints, use),
            state_version=session.state_version + 1,
        )
        return updated, hint

    def _finish_if_target(self, session: GameSession) -> tuple[GameSession, bool, float]:
        elapsed = max(0.0, (datetime.now(UTC) - session.started_at).total_seconds())
        if session.navigation.current_id != session.round.target_id:
            return session, False, elapsed
        score = calculate_score(
            session.round.optimal_distance,
            session.navigation.moves,
            elapsed,
            session.round.time_window,
            session.hint_penalty,
        )
        return (
            replace(
                session,
                status=SessionStatus.COMPLETED,
                completed_at=datetime.now(UTC),
                final_score=score.total,
            ),
            True,
            elapsed,
        )

    async def _select_round(
        self,
        mode: SessionMode,
        round_id: str | None,
        category: str | None,
        difficulty: Difficulty | None,
    ) -> tuple[Round, date | None]:
        if mode is SessionMode.DAILY:
            assignment, round_ = await self._daily.assignment()
            return round_, assignment.day
        if round_id is not None:
            round_ = self._graph.get_round(round_id)
            if round_ is None or not round_.published:
                raise NotFoundError("Published round not found")
            return round_, None
        rounds = self._graph.list_published_rounds(category=category, difficulty=difficulty)
        if not rounds:
            raise NotFoundError("No published round matches those filters")
        return rounds[0], None
