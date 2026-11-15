"""The one place where domain errors become HTTP responses (see `spec/00-overview.md`)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from taskapp.domain.errors import (
    DomainError,
    EmailTaken,
    InvalidCredentials,
    InvalidToken,
    InvalidTransition,
    PermissionDenied,
    TaskNotFound,
    UserNotFound,
    ValidationError,
)

# error class -> (HTTP status, machine code, fixed message or None to use the error's own text).
# Fixed messages keep authentication failures from saying why they failed.
_MAPPING: dict[type[DomainError], tuple[int, str, str | None]] = {
    ValidationError: (422, "validation_error", None),
    EmailTaken: (409, "email_taken", "This email is already registered"),
    InvalidCredentials: (401, "invalid_credentials", "Invalid email or password"),
    InvalidToken: (401, "invalid_token", "Not authenticated"),
    TaskNotFound: (404, "task_not_found", "Task not found"),
    UserNotFound: (404, "user_not_found", "User not found"),
    PermissionDenied: (403, "permission_denied", None),
    InvalidTransition: (409, "invalid_transition", None),
}


def _body(code: str, message: str, details: list[object]) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "details": details}}


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    for cls in type(exc).__mro__:
        if cls in _MAPPING:
            status, code, message = _MAPPING[cls]
            break
    else:
        status, code, message = 500, "internal_error", "Something went wrong"
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(_body(code, message or str(exc), []), status_code=status, headers=headers)


async def _request_validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    details: list[object] = [
        {"location": [str(part) for part in error["loc"]], "message": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        _body("validation_error", "The request is not valid", details), status_code=422
    )


async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # The details stay in the server log (the exception is still raised to the server);
    # the client only learns that something went wrong.
    return JSONResponse(_body("internal_error", "Something went wrong", []), status_code=500)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, _unexpected_error)
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _request_validation_error)
