"""SQL row/domain mapping tests require no PostgreSQL service."""

from datetime import UTC, date, datetime

from webwoven_api.daily.models import DailyScore
from webwoven_api.guests.models import Guest
from webwoven_api.persistence.postgres.daily import score_from_row
from webwoven_api.persistence.postgres.guests import guest_from_row
from webwoven_api.persistence.postgres.locking import advisory_key
from webwoven_api.persistence.postgres.models import DailyScoreRow, GuestRow

NOW = datetime(2026, 7, 13, 8, tzinfo=UTC)


def test_guest_row_maps_without_losing_csrf_token() -> None:
    guest = Guest("guest-1", "Atlas", "csrf-secret", NOW, NOW)
    row = GuestRow(
        id=guest.id,
        display_name=guest.display_name,
        csrf_token=guest.csrf_token,
        created_at=guest.created_at,
        updated_at=guest.updated_at,
    )
    assert guest_from_row(row) == guest


def test_daily_score_row_maps_milliseconds_and_current_name() -> None:
    row = DailyScoreRow(
        day=date(2026, 7, 13),
        session_id="session-1",
        guest_id="guest-1",
        score=900,
        moves=4,
        hints_used=1,
        elapsed_ms=12_345,
        completed_at=NOW,
    )
    assert score_from_row(row, "Atlas") == DailyScore(
        day=row.day,
        session_id=row.session_id,
        guest_id=row.guest_id,
        display_name="Atlas",
        score=900,
        moves=4,
        hints_used=1,
        elapsed_seconds=12.345,
        completed_at=NOW,
    )


def test_advisory_keys_are_stable_and_scope_separated() -> None:
    assert advisory_key("session", "same") == advisory_key("session", "same")
    assert advisory_key("session", "same") != advisory_key("daily", "same")
