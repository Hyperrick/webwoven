"""Session state and versioned command outcomes."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from webwoven_api.domain.hints import HintOutcome, HintResult, HintType
from webwoven_api.domain.navigation import NavigationState
from webwoven_api.graph.contracts import Round
from webwoven_api.sessions.exploration import DecisionFrame


class SessionMode(StrEnum):
    SOLO = "solo"
    DAILY = "daily"
    RELAY = "relay"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class HintUse:
    hint_type: HintType
    penalty: int
    relation_key: str | None
    entity_id: str | None
    message: str
    used_at: datetime
    outcome: HintOutcome | None = None


@dataclass(frozen=True, slots=True)
class GameSession:
    id: str
    guest_id: str
    mode: SessionMode
    graph_version: str
    round: Round
    navigation: NavigationState
    status: SessionStatus
    state_version: int
    started_at: datetime
    decision_history: tuple[DecisionFrame, ...] = ()
    hints: tuple[HintUse, ...] = ()
    completed_at: datetime | None = None
    final_score: int | None = None
    room_code: str | None = None
    daily_day: date | None = None

    @property
    def hint_penalty(self) -> int:
        return sum(hint.penalty for hint in self.hints)


@dataclass(frozen=True, slots=True)
class CommandExecution:
    session: GameSession
    applied: bool
    duplicate: bool = False
    hint: HintResult | None = None


@dataclass(frozen=True, slots=True)
class FollowEdgeCommand:
    command_id: str
    expected_state_version: int
    edge_token: str


@dataclass(frozen=True, slots=True)
class BackCommand:
    command_id: str
    expected_state_version: int


@dataclass(frozen=True, slots=True)
class UseHintCommand:
    command_id: str
    expected_state_version: int
    hint_type: HintType
    relation_key: str | None
    entity_id: str | None


SessionCommand = FollowEdgeCommand | BackCommand | UseHintCommand
