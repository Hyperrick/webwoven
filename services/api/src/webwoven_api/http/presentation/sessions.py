"""Route Race session wire presentation."""

from base64 import urlsafe_b64encode
from collections import defaultdict
from typing import Literal

from webwoven_api.domain.hints import HintResult
from webwoven_api.graph.contracts import GraphEdge, GraphReader, RelationDirection
from webwoven_api.http.contracts.common import EntityResponse
from webwoven_api.http.contracts.sessions import (
    DecisionChoiceResponse,
    DecisionConnectionResponse,
    DecisionRelationResponse,
    DecisionStageResponse,
    EdgeTargetResponse,
    HintResponse,
    HintUseResponse,
    RelationGroupResponse,
    SessionSnapshot,
)
from webwoven_api.http.presentation.entities import entity_response
from webwoven_api.sessions.exploration import DecisionAction, DecisionFrame
from webwoven_api.sessions.frontier import playable_edges_for
from webwoven_api.sessions.models import GameSession, HintUse, SessionStatus
from webwoven_api.sessions.service import SessionService


class SessionPresenter:
    def __init__(self, graph: GraphReader, sessions: SessionService) -> None:
        self._graph = graph
        self._sessions = sessions

    def snapshot(self, session: GameSession) -> SessionSnapshot:
        grouped: defaultdict[tuple[str, RelationDirection, str], list[EdgeTargetResponse]] = (
            defaultdict(list)
        )
        if session.status is SessionStatus.ACTIVE:
            self._group_playable_edges(session, grouped)
        return SessionSnapshot(
            id=session.id,
            mode=session.mode,
            status=session.status,
            graph_version=session.graph_version,
            round_id=session.round.id,
            category=session.round.category,
            difficulty=session.round.difficulty,
            optimal_distance=session.round.optimal_distance,
            start=self._entity(session.round.start_id),
            target=self._entity(session.round.target_id),
            current=self._entity(session.navigation.current_id),
            navigation_stack=[self._entity(entity_id) for entity_id in session.navigation.stack],
            trail=[self._entity(entity_id) for entity_id in session.navigation.trail],
            decision_history=self._decision_history(session),
            moves=session.navigation.moves,
            hints_used=[_hint_use_response(hint) for hint in session.hints],
            hint_penalty=session.hint_penalty,
            state_version=session.state_version,
            started_at=session.started_at,
            completed_at=session.completed_at,
            final_score=session.final_score,
            daily_day=session.daily_day,
            relation_groups=_relation_groups(grouped),
        )

    def _group_playable_edges(
        self,
        session: GameSession,
        grouped: defaultdict[tuple[str, RelationDirection, str], list[EdgeTargetResponse]],
    ) -> None:
        for edge in playable_edges_for(self._graph, session.round, session.navigation):
            grouped[(edge.relation_key, edge.direction, edge.relation_label)].append(
                EdgeTargetResponse(
                    edge_token=self._sessions.issue_edge_token(session, edge.id),
                    explanation=edge.explanation,
                    target=entity_response(edge.target),
                )
            )

    def _decision_history(self, session: GameSession) -> list[DecisionStageResponse]:
        return [
            self._decision_stage(index, frame)
            for index, frame in enumerate(session.decision_history)
        ]

    def _decision_stage(self, index: int, frame: DecisionFrame) -> DecisionStageResponse:
        edges = self._pinned_edges(frame)
        selected_edge = _selected_edge(frame, edges)
        choices, selected_choice_id = _decision_choices(index, frame, edges, selected_edge)
        if frame.action is DecisionAction.FOLLOW and selected_choice_id is None:
            raise RuntimeError("Follow decision does not identify a selected choice")
        action: Literal["follow", "back"] = (
            "follow" if frame.action is DecisionAction.FOLLOW else "back"
        )
        return DecisionStageResponse(
            index=index,
            source=self._entity(frame.source_id),
            destination=self._entity(frame.destination_id),
            action=action,
            choices=choices,
            selected_choice_id=selected_choice_id,
        )

    def _pinned_edges(self, frame: DecisionFrame) -> tuple[GraphEdge, ...]:
        source_edges = {edge.id: edge for edge in self._graph.get_edges(frame.source_id)}
        edges: list[GraphEdge] = []
        for edge_id in frame.visible_edge_ids:
            edge = source_edges.get(edge_id)
            if edge is None:
                raise RuntimeError(f"Pinned decision edge is missing: {edge_id}")
            edges.append(edge)
        return tuple(edges)

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


def _relation_groups(
    grouped: defaultdict[tuple[str, RelationDirection, str], list[EdgeTargetResponse]],
) -> list[RelationGroupResponse]:
    return [
        RelationGroupResponse(
            group_id=_relation_group_id(key, direction, label),
            property_id=key,
            label=label,
            direction=direction,
            edges=edges,
        )
        for (key, direction, label), edges in sorted(grouped.items())
    ]


def _hint_use_response(hint: HintUse) -> HintUseResponse:
    return HintUseResponse(
        hint_type=hint.hint_type,
        penalty=hint.penalty,
        relation_property_id=hint.relation_key,
        entity_qid=hint.entity_id,
        message=hint.message,
        used_at=hint.used_at,
    )


def _selected_edge(frame: DecisionFrame, edges: tuple[GraphEdge, ...]) -> GraphEdge | None:
    if frame.selected_edge_id is None:
        return None
    selected = next((edge for edge in edges if edge.id == frame.selected_edge_id), None)
    if selected is None:
        raise RuntimeError("Pinned selected edge is missing from its decision frontier")
    return selected


def _decision_choices(
    index: int,
    frame: DecisionFrame,
    edges: tuple[GraphEdge, ...],
    selected_edge: GraphEdge | None,
) -> tuple[list[DecisionChoiceResponse], str | None]:
    by_target: dict[str, list[GraphEdge]] = {}
    for edge in edges:
        by_target.setdefault(edge.target_id, []).append(edge)

    choices: list[DecisionChoiceResponse] = []
    selected_choice_id = None
    for target_id, target_edges in sorted(by_target.items()):
        ordered_edges = sorted(target_edges, key=_historical_edge_key)
        primary = _primary_edge(ordered_edges, selected_edge)
        choice_id = _decision_choice_id(index, frame.source_id, target_id)
        choices.append(
            DecisionChoiceResponse(
                id=choice_id,
                target=entity_response(primary.target),
                relation=_decision_relation(primary),
                statement=primary.explanation,
                connections=[
                    DecisionConnectionResponse(
                        id=_decision_connection_id(index, frame.source_id, edge.id),
                        relation=_decision_relation(edge),
                        statement=edge.explanation,
                    )
                    for edge in ordered_edges
                ],
            )
        )
        if selected_edge is not None and selected_edge.target_id == target_id:
            selected_choice_id = choice_id
    return choices, selected_choice_id


def _primary_edge(ordered_edges: list[GraphEdge], selected_edge: GraphEdge | None) -> GraphEdge:
    if selected_edge is not None and selected_edge.target_id == ordered_edges[0].target_id:
        return selected_edge
    return ordered_edges[0]


def _decision_relation(edge: GraphEdge) -> DecisionRelationResponse:
    return DecisionRelationResponse(
        property_id=edge.relation_key,
        label=edge.relation_label,
        direction=edge.direction,
    )


def _relation_group_id(property_id: str, direction: RelationDirection, label: str) -> str:
    """Return a stable, DOM-safe identity without replacing the semantic property ID."""
    encoded_label = urlsafe_b64encode(label.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{property_id}-{direction}-{encoded_label}"


def _historical_edge_key(edge: GraphEdge) -> tuple[str, str, str, str, str, str]:
    return (
        edge.target_id,
        edge.relation_key,
        edge.direction,
        edge.relation_label,
        edge.explanation,
        edge.id,
    )


def _decision_choice_id(index: int, source_id: str, target_id: str) -> str:
    return f"decision:{index}:{source_id}:{target_id}"


def _decision_connection_id(index: int, source_id: str, edge_id: str) -> str:
    return f"connection:{index}:{source_id}:{edge_id}"
