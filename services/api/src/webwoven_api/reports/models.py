"""Moderation report state."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ContentReport:
    id: str
    guest_id: str
    entity_id: str | None
    edge_id: str | None
    round_id: str | None
    reason: str
    details: str
    created_at: datetime
