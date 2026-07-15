"""Guest identity creation and profile rules."""

import secrets
import unicodedata
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from webwoven_api.domain.errors import DomainError, NotFoundError
from webwoven_api.guests.models import Guest
from webwoven_api.guests.repository import GuestRepository

_ALLOWED_PUNCTUATION = {" ", "'", "’", "-"}
_RESERVED_WORDS = {"admin", "moderator", "system", "webwoven"}


class GuestService:
    def __init__(self, repository: GuestRepository) -> None:
        self._repository = repository

    async def create(self, display_name: str | None = None) -> Guest:
        guest_id = str(uuid4())
        name = normalize_display_name(display_name or default_display_name(guest_id))
        guest = Guest.now(
            guest_id=guest_id,
            display_name=name,
            csrf_token=secrets.token_urlsafe(24),
        )
        await self._repository.create(guest)
        return guest

    async def get(self, guest_id: str) -> Guest:
        guest = await self._repository.get(guest_id)
        if guest is None:
            raise NotFoundError("Guest not found")
        return guest

    async def update_name(self, guest_id: str, display_name: str) -> Guest:
        guest = await self.get(guest_id)
        updated = replace(
            guest,
            display_name=normalize_display_name(display_name),
            updated_at=datetime.now(UTC),
        )
        await self._repository.save(updated)
        return updated


def normalize_display_name(value: str) -> str:
    name = unicodedata.normalize("NFKC", " ".join(value.split()))
    if not 2 <= len(name) <= 24:
        raise DomainError("invalid_display_name", "Display name must be 2–24 characters.")
    if not name[0].isalnum() or not name[-1].isalnum():
        raise DomainError(
            "invalid_display_name",
            "Display name must begin and end with a letter or number.",
        )
    if any(not character.isalnum() and character not in _ALLOWED_PUNCTUATION for character in name):
        raise DomainError(
            "invalid_display_name",
            "Use letters, numbers, spaces, apostrophes, or hyphens only.",
        )
    words = {
        word.casefold()
        for word in name.replace("-", " ").replace("'", " ").replace("’", " ").split()
    }
    if words & _RESERVED_WORDS:
        raise DomainError(
            "reserved_display_name",
            "Choose a name that does not imply an official Webwoven role.",
        )
    return name


def default_display_name(guest_id: str) -> str:
    return f"Explorer {guest_id[:4].upper()}"
