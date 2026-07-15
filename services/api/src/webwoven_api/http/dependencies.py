"""FastAPI dependency adapters for the explicit application container."""

from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from webwoven_api.container import AppContainer
from webwoven_api.domain.errors import ForbiddenError, NotFoundError
from webwoven_api.guests.models import Guest


def get_container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


ContainerDependency = Annotated[AppContainer, Depends(get_container)]


async def current_guest(
    request: Request,
    container: ContainerDependency,
) -> Guest:
    cached = getattr(request.state, "authenticated_guest", None)
    if isinstance(cached, Guest):
        return cached
    guest_cookie = request.cookies.get(container.settings.cookie_name)
    if guest_cookie is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Create a guest identity first")
    try:
        guest_id = container.guest_cookies.verify(guest_cookie)
        return await container.guests.get(guest_id)
    except (ForbiddenError, NotFoundError) as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Guest identity is invalid") from error


GuestDependency = Annotated[Guest, Depends(current_guest)]


async def optional_current_guest(
    request: Request,
    container: ContainerDependency,
) -> Guest | None:
    """Resolve a signed guest when present without requiring one for public reads."""
    guest_cookie = request.cookies.get(container.settings.cookie_name)
    if guest_cookie is None:
        return None
    try:
        guest_id = container.guest_cookies.verify(guest_cookie)
        return await container.guests.get(guest_id)
    except (ForbiddenError, NotFoundError):
        return None


OptionalGuestDependency = Annotated[Guest | None, Depends(optional_current_guest)]
