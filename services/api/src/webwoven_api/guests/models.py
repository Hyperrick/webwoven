"""Guest identity state."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class Guest:
    id: str
    display_name: str
    csrf_token: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def now(
        cls,
        *,
        guest_id: str,
        display_name: str,
        csrf_token: str,
    ) -> "Guest":
        now = datetime.now(UTC)
        return cls(guest_id, display_name, csrf_token, now, now)
