"""Daily ranking keeps pseudonymous guests distinct and resolves current names."""

from datetime import UTC, date, datetime, timedelta

import pytest
from webwoven_api.daily.models import DailyScore
from webwoven_api.guests.models import Guest
from webwoven_api.persistence.memory.daily import MemoryDailyRepository
from webwoven_api.persistence.memory.guests import MemoryGuestRepository

DAY = date(2026, 7, 15)
NOW = datetime(2026, 7, 15, 8, tzinfo=UTC)


def _guest(guest_id: str, name: str) -> Guest:
    return Guest(guest_id, name, f"csrf-{guest_id}", NOW, NOW)


def _score(
    guest_id: str,
    name: str,
    score: int,
    *,
    elapsed: float = 30,
    moves: int = 4,
    offset: int = 0,
) -> DailyScore:
    return DailyScore(
        day=DAY,
        session_id=f"session-{guest_id}",
        guest_id=guest_id,
        display_name=name,
        score=score,
        moves=moves,
        hints_used=0,
        elapsed_seconds=elapsed,
        completed_at=NOW + timedelta(seconds=offset),
    )


@pytest.mark.asyncio
async def test_top_scores_and_current_rank_are_independent() -> None:
    guests = MemoryGuestRepository()
    daily = MemoryDailyRepository(guests)
    for index in range(25):
        guest_id = f"guest-{index:02}"
        name = "Same Name" if index in {0, 24} else f"Explorer {index:02}"
        await guests.create(_guest(guest_id, name))
        await daily.save_score(_score(guest_id, name, 1000 - index, offset=index))

    leaders = await daily.list_scores(DAY, 20)
    current = await daily.get_ranked_score(DAY, "guest-24")

    assert len(leaders) == 20
    assert current is not None
    assert current.rank == 25
    assert current.score.display_name == "Same Name"
    assert leaders[0].guest_id == "guest-00"


@pytest.mark.asyncio
async def test_ties_are_stable_and_renames_update_existing_scores() -> None:
    guests = MemoryGuestRepository()
    daily = MemoryDailyRepository(guests)
    for guest_id in ("guest-b", "guest-a"):
        await guests.create(_guest(guest_id, "Duplicate"))
        await daily.save_score(_score(guest_id, "Duplicate", 900))

    renamed = _guest("guest-b", "Fresh Name")
    await guests.save(renamed)
    leaders = await daily.list_scores(DAY, 20)

    assert [score.guest_id for score in leaders] == ["guest-a", "guest-b"]
    assert leaders[1].display_name == "Fresh Name"
