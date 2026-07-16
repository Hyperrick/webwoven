"""Guest profile request and response contracts."""

import unicodedata

from pydantic import Field, field_validator

from webwoven_api.http.contracts.common import ApiModel


class _GuestNameRequest(ApiModel):
    @field_validator("display_name", mode="before", check_fields=False)
    @classmethod
    def normalize_whitespace(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return unicodedata.normalize("NFKC", " ".join(value.split()))


class GuestCreateRequest(_GuestNameRequest):
    display_name: str | None = Field(default=None, min_length=2, max_length=24)


class GuestUpdateRequest(_GuestNameRequest):
    display_name: str = Field(min_length=2, max_length=24)


class GuestResponse(ApiModel):
    id: str
    display_name: str
    csrf_token: str
