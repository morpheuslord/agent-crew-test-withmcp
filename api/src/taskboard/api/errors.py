"""The one place where domain errors become HTTP responses."""

import logging
from typing import Final

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from taskboard.domain.errors import (
    AuthenticationRequiredError,
    ConflictError,
    DomainError,
    InvalidCredentialsError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    ProjectArchivedError,
    RateLimitedError,
    ValidationFailedError,
)
from taskboard.logging_setup import request_id_var

logger = logging.getLogger("taskboard.errors")

STATUS_BY_ERROR: Final[dict[type[DomainError], int]] = {
    ValidationFailedError: 422,
    AuthenticationRequiredError: 401,
    InvalidCredentialsError: 401,
    PermissionDeniedError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    ProjectArchivedError: 409,
    PayloadTooLargeError: 413,
    RateLimitedError: 429,
}


def error_response(
    status: int, code: str, message: str, fields: list[dict[str, str]] | None = None
) -> JSONResponse:
    body: dict[str, object] = {
        "code": code,
        "message": message,
        "request_id": request_id_var.get(),
    }
    if fields is not None:
        body["fields"] = fields
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse({"error": body}, status_code=status, headers=headers)


def _status_for(exc: DomainError) -> int:
    for cls in type(exc).__mro__:
        if cls in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[cls]
    return 400


async def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    return error_response(_status_for(exc), exc.code, exc.message)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    fields = [
        {
            "field": ".".join(str(p) for p in err.get("loc", ()) if p != "body"),
            "message": str(err.get("msg", "Invalid value")),
        }
        for err in exc.errors()
    ]
    return error_response(422, "validation_failed", "The request is invalid.", fields)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    code = "not_found" if exc.status_code == 404 else "http_error"
    return error_response(exc.status_code, code, str(exc.detail))


async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error", exc_info=exc)
    return error_response(500, "internal_error", "Something went wrong. Quote the request id.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected)
