"""PostgreSQL guest-identity repository."""

from sqlalchemy import select

from webwoven_api.guests.models import Guest
from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.models import GuestRow


class PostgresGuestRepository:
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def create(self, guest: Guest) -> None:
        async with self._database.session() as session:
            session.add(_row_from_guest(guest))

    async def get(self, guest_id: str) -> Guest | None:
        async with self._database.session() as session:
            row = await session.scalar(select(GuestRow).where(GuestRow.id == guest_id))
            return guest_from_row(row) if row is not None else None

    async def save(self, guest: Guest) -> None:
        async with self._database.session() as session:
            row = await session.scalar(
                select(GuestRow).where(GuestRow.id == guest.id).with_for_update()
            )
            if row is None:
                session.add(_row_from_guest(guest))
                return
            row.display_name = guest.display_name
            row.csrf_token = guest.csrf_token
            row.updated_at = guest.updated_at


def guest_from_row(row: GuestRow) -> Guest:
    return Guest(
        id=row.id,
        display_name=row.display_name,
        csrf_token=row.csrf_token,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _row_from_guest(guest: Guest) -> GuestRow:
    return GuestRow(
        id=guest.id,
        display_name=guest.display_name,
        csrf_token=guest.csrf_token,
        created_at=guest.created_at,
        updated_at=guest.updated_at,
    )
