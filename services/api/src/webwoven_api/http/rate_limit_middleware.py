"""Action-specific HTTP rate-limit enforcement."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import cast

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from webwoven_api.container import AppContainer
from webwoven_api.http.rate_limit_identity import request_rate_identity

RequestHandler = Callable[[Request], Awaitable[Response]]


@dataclass(frozen=True, slots=True)
class _Policy:
    scope: str
    limit: int
    prefer_guest: bool = True


class RequestRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        container = cast(AppContainer, request.app.state.container)
        policy = _policy_for(request, container)
        if policy is None:
            return await call_next(request)
        identity = request_rate_identity(
            request,
            cookie_name=container.settings.cookie_name,
            signer=container.guest_cookies,
            hmac_secret=container.settings.session_secret,
            prefer_guest=policy.prefer_guest,
        )
        try:
            decision = await container.rate_limiter.check(
                scope=policy.scope,
                identity=identity,
                limit=policy.limit,
                window_seconds=container.settings.rate_limit_window_seconds,
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"code": "rate_limit_unavailable", "message": "Please try again."},
            )
        if not decision.allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(decision.retry_after_seconds)},
                content={"code": "rate_limited", "message": "Too many requests."},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        return response


def _policy_for(request: Request, container: AppContainer) -> _Policy | None:
    path = request.url.path.rstrip("/")
    settings = container.settings
    if request.method == "PATCH" and path == "/api/v1/guests/me":
        return _Policy("guest-update", settings.rate_limit_guest_updates)
    if request.method == "GET" and path.startswith("/api/v1/rooms/") and path.endswith("/invite"):
        return _Policy("room-invite", settings.rate_limit_room_invites)
    if request.method != "POST":
        return None
    if path == "/api/v1/guests":
        return _Policy("guest-create", settings.rate_limit_guest_creates, False)
    if path == "/api/v1/sessions":
        return _Policy("session-create", settings.rate_limit_session_creates)
    if path.endswith("/commands") and path.startswith("/api/v1/sessions/"):
        return _Policy("session-command", settings.rate_limit_session_commands)
    if path == "/api/v1/rooms":
        return _Policy("room-create", settings.rate_limit_room_creates)
    if path.startswith("/api/v1/rooms/") and path.endswith(("/join", "/start", "/rematch")):
        return _Policy("room-action", settings.rate_limit_room_actions)
    if path.startswith("/api/v1/rooms/") and path.endswith("/ready"):
        return _Policy("room-ready", settings.rate_limit_room_ready)
    if path == "/api/v1/content-reports":
        return _Policy("content-report", settings.rate_limit_content_reports)
    return None
