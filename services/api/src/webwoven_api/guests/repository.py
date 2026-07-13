"""Persistence boundary owned by guest identity."""

from typing import Protocol

from webwoven_api.guests.models import Guest


class GuestRepository(Protocol):
    async def create(self, guest: Guest) -> None: ...

    async def get(self, guest_id: str) -> Guest | None: ...

    async def save(self, guest: Guest) -> None: ...
