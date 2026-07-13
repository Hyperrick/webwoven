"""Guest identity routes."""

from fastapi import APIRouter, Response, status

from webwoven_api.http.contracts.guests import (
    GuestCreateRequest,
    GuestResponse,
    GuestUpdateRequest,
)
from webwoven_api.http.dependencies import ContainerDependency, GuestDependency

router = APIRouter(prefix="/api/v1/guests", tags=["guests"])


@router.post("", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
async def create_guest(
    body: GuestCreateRequest,
    response: Response,
    container: ContainerDependency,
) -> GuestResponse:
    guest = await container.guests.create(body.display_name)
    response.set_cookie(
        container.settings.cookie_name,
        container.guest_cookies.issue(guest.id),
        httponly=True,
        secure=container.settings.cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    response.set_cookie(
        container.settings.csrf_cookie_name,
        guest.csrf_token,
        httponly=False,
        secure=container.settings.cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return GuestResponse(id=guest.id, display_name=guest.display_name, csrf_token=guest.csrf_token)


@router.get("/me", response_model=GuestResponse)
async def get_guest(guest: GuestDependency) -> GuestResponse:
    """Resume the signed guest identity without replacing its cookie."""
    return GuestResponse(
        id=guest.id,
        display_name=guest.display_name,
        csrf_token=guest.csrf_token,
    )


@router.patch("/me", response_model=GuestResponse)
async def update_guest(
    body: GuestUpdateRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> GuestResponse:
    updated = await container.guests.update_name(guest.id, body.display_name)
    return GuestResponse(
        id=updated.id,
        display_name=updated.display_name,
        csrf_token=updated.csrf_token,
    )
