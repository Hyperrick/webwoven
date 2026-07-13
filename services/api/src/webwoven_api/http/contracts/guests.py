"""Guest profile request and response contracts."""

from pydantic import Field

from webwoven_api.http.contracts.common import ApiModel


class GuestCreateRequest(ApiModel):
    display_name: str | None = Field(default=None, max_length=64)


class GuestUpdateRequest(ApiModel):
    display_name: str = Field(min_length=1, max_length=64)


class GuestResponse(ApiModel):
    id: str
    display_name: str
    csrf_token: str
