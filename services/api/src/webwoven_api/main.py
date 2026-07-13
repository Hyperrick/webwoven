"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ExceptionHandler

from webwoven_api import __version__
from webwoven_api.container import AppContainer, build_container
from webwoven_api.domain.errors import DomainError, ForbiddenError, NotFoundError
from webwoven_api.http.error_handlers import (
    domain_error_handler,
    forbidden_handler,
    not_found_handler,
)
from webwoven_api.http.rate_limit_middleware import RequestRateLimitMiddleware
from webwoven_api.http.routes import daily, guests, reports, rooms, sessions, system
from webwoven_api.http.security_middleware import RequestSecurityMiddleware
from webwoven_api.http.websocket import router as websocket_router
from webwoven_api.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings()
    application = FastAPI(
        title="Webwoven API",
        summary="Server-authoritative knowledge graph game API",
        version=__version__,
        docs_url="/api/docs" if configured.environment != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=_lifespan,
    )
    application.state.container = build_container(configured)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[configured.origin, configured.api_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )
    application.add_middleware(RequestSecurityMiddleware, settings=configured)
    application.add_middleware(RequestRateLimitMiddleware)
    application.add_exception_handler(DomainError, cast(ExceptionHandler, domain_error_handler))
    application.add_exception_handler(NotFoundError, cast(ExceptionHandler, not_found_handler))
    application.add_exception_handler(ForbiddenError, cast(ExceptionHandler, forbidden_handler))
    application.include_router(system.router)
    application.include_router(guests.router)
    application.include_router(daily.router)
    application.include_router(sessions.router)
    application.include_router(rooms.router)
    application.include_router(reports.router)
    application.include_router(websocket_router)
    return application


@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncGenerator[None]:
    container = cast(AppContainer, application.state.container)
    try:
        await container.start()
        yield
    finally:
        await container.close()


app = create_app()
