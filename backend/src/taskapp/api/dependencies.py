from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from taskapp.application.authenticate_user import AuthenticateUser
from taskapp.application.ports import Clock, Notifier, PasswordHasher, TokenService, UnitOfWork
from taskapp.domain.errors import InvalidToken
from taskapp.domain.user import User


@dataclass(frozen=True)
class Dependencies:
    """What the routes need from the outside world; built in the composition root."""

    uow_factory: Callable[[], UnitOfWork]
    hasher: PasswordHasher
    tokens: TokenService
    clock: Clock
    notifier: Notifier
    shutdown: Callable[[], Awaitable[None]] | None = None


def get_dependencies(request: Request) -> Dependencies:
    dependencies = request.app.state.dependencies
    if not isinstance(dependencies, Dependencies):
        raise RuntimeError("the app was created without dependencies")
    return dependencies


# `auto_error=False` so a missing or non-bearer header goes through the uniform error body.
_bearer = HTTPBearer(auto_error=False)


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    dependencies: Annotated[Dependencies, Depends(get_dependencies)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise InvalidToken("no bearer token")
    return await AuthenticateUser(dependencies.uow_factory(), dependencies.tokens).execute(
        credentials.credentials
    )
