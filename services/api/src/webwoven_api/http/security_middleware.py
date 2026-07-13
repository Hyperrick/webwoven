"""Origin validation and double-submit CSRF protection for unsafe API calls."""

import hmac
from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from webwoven_api.container import AppContainer
from webwoven_api.domain.errors import ForbiddenError, NotFoundError
from webwoven_api.settings import Settings

RequestHandler = Callable[[Request], Awaitable[Response]]


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._origins = {settings.origin.rstrip("/"), settings.api_origin.rstrip("/")}

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        if not _requires_protection(request):
            return await call_next(request)
        origin = request.headers.get("origin")
        if origin is None or origin.rstrip("/") not in self._origins:
            return _security_error(status.HTTP_403_FORBIDDEN, "origin_rejected", "Origin rejected")
        cookie_token = request.cookies.get(self._settings.csrf_cookie_name)
        header_token = request.headers.get("x-csrf-token")
        if (
            cookie_token is None
            or header_token is None
            or not hmac.compare_digest(cookie_token, header_token)
        ):
            return _security_error(
                status.HTTP_403_FORBIDDEN,
                "csrf_rejected",
                "CSRF token is missing or invalid",
            )
        container = cast(AppContainer, request.app.state.container)
        guest_cookie = request.cookies.get(self._settings.cookie_name)
        if guest_cookie is None:
            return _security_error(
                status.HTTP_403_FORBIDDEN,
                "csrf_rejected",
                "CSRF token is missing or invalid",
            )
        try:
            guest_id = container.guest_cookies.verify(guest_cookie)
            guest = await container.guests.get(guest_id)
        except (ForbiddenError, NotFoundError):
            return _security_error(
                status.HTTP_403_FORBIDDEN,
                "csrf_rejected",
                "CSRF token is missing or invalid",
            )
        if not hmac.compare_digest(cookie_token, guest.csrf_token):
            return _security_error(
                status.HTTP_403_FORBIDDEN,
                "csrf_rejected",
                "CSRF token is missing or invalid",
            )
        request.state.authenticated_guest = guest
        return await call_next(request)


def _requires_protection(request: Request) -> bool:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    path = request.url.path.rstrip("/")
    return path.startswith("/api/") and path != "/api/v1/guests"


def _security_error(status_code: int, code: str, message: str) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content={"code": code, "message": message})
