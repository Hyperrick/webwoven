"""Daily assignment and score records."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class DailyAssignment:
    day: date
    graph_version: str
    round_id: str


@dataclass(frozen=True, slots=True)
class DailyScore:
    day: date
    session_id: str
    guest_id: str
    display_name: str
    score: int
    moves: int
    hints_used: int
    elapsed_seconds: float
    completed_at: datetime
