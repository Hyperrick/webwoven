"""Concurrency-safe in-memory guest repository."""

import asyncio

from webwoven_api.guests.models import Guest


class MemoryGuestRepository:
    def __init__(self) -> None:
        self._guests: dict[str, Guest] = {}
        self._lock = asyncio.Lock()

    async def create(self, guest: Guest) -> None:
        async with self._lock:
            self._guests[guest.id] = guest

    async def get(self, guest_id: str) -> Guest | None:
        async with self._lock:
            return self._guests.get(guest_id)

    async def save(self, guest: Guest) -> None:
        async with self._lock:
            self._guests[guest.id] = guest
