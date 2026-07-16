"""Route Race session and command wire contracts."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field

from webwoven_api.domain.hints import HintOutcome, HintType
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import RelationDirection
from webwoven_api.http.contracts.common import ApiModel, EntityResponse
from webwoven_api.sessions.models import SessionMode, SessionStatus


class SessionCreateRequest(ApiModel):
    mode: SessionMode = SessionMode.SOLO
    round_id: str | None = None
    category: str | None = None
    difficulty: Difficulty | None = None


class FollowEdgeRequest(ApiModel):
    type: Literal["follow_edge"]
    client_command_id: str = Field(min_length=1, max_length=100)
    expected_state_version: int = Field(ge=0)
    edge_token: str = Field(min_length=20, max_length=2048)


class BackRequest(ApiModel):
    type: Literal["back"]
    client_command_id: str = Field(min_length=1, max_length=100)
    expected_state_version: int = Field(ge=0)


class UseHintRequest(ApiModel):
    type: Literal["use_hint"]
    client_command_id: str = Field(min_length=1, max_length=100)
    expected_state_version: int = Field(ge=0)
    hint_type: HintType
    relation_property_id: str | None = None
    entity_qid: str | None = None


SessionCommandRequest = Annotated[
    FollowEdgeRequest | BackRequest | UseHintRequest,
    Field(discriminator="type"),
]


class EdgeTargetResponse(ApiModel):
    edge_token: str
    explanation: str
    target: EntityResponse


class RelationGroupResponse(ApiModel):
    group_id: str
    property_id: str
    label: str
    direction: RelationDirection
    edges: list[EdgeTargetResponse]


class HintUseResponse(ApiModel):
    hint_type: HintType
    penalty: int
    relation_property_id: str | None
    entity_qid: str | None
    message: str
    used_at: datetime
    outcome: HintOutcome | None = None


class HintResponse(ApiModel):
    hint_type: HintType
    penalty: int
    relation_property_id: str | None
    entity_qid: str | None
    message: str
    outcome: HintOutcome | None = None


class DecisionRelationResponse(ApiModel):
    property_id: str
    label: str
    direction: RelationDirection


class DecisionConnectionResponse(ApiModel):
    id: str
    relation: DecisionRelationResponse
    statement: str


class DecisionChoiceResponse(ApiModel):
    id: str
    target: EntityResponse
    relation: DecisionRelationResponse
    statement: str
    connections: list[DecisionConnectionResponse]


class DecisionStageResponse(ApiModel):
    index: int = Field(ge=0)
    source: EntityResponse
    destination: EntityResponse
    action: Literal["follow", "back"]
    choices: list[DecisionChoiceResponse]
    selected_choice_id: str | None = None


class SessionSnapshot(ApiModel):
    id: str
    mode: SessionMode
    status: SessionStatus
    graph_version: str
    round_id: str
    category: str
    difficulty: Difficulty
    optimal_distance: int
    start: EntityResponse
    target: EntityResponse
    current: EntityResponse
    navigation_stack: list[EntityResponse]
    trail: list[EntityResponse]
    decision_history: list[DecisionStageResponse]
    moves: int
    hints_used: list[HintUseResponse]
    hint_penalty: int
    state_version: int
    started_at: datetime
    completed_at: datetime | None
    final_score: int | None
    daily_day: date | None
    relation_groups: list[RelationGroupResponse]


class CommandResponse(ApiModel):
    applied: bool
    duplicate: bool
    hint: HintResponse | None
    session: SessionSnapshot


class StaleCommandResponse(ApiModel):
    code: Literal["stale_state"] = "stale_state"
    message: str
    current: SessionSnapshot
