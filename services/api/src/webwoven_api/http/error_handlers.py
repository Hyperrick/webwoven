"""Translate domain failures into stable API errors."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from webwoven_api.domain.errors import DomainError, ForbiddenError, NotFoundError


async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"code": error.code, "message": error.message},
    )


async def not_found_handler(request: Request, error: NotFoundError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": "not_found", "message": str(error)},
    )


async def forbidden_handler(request: Request, error: ForbiddenError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"code": "forbidden", "message": str(error)},
    )
