from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Request

from taskapp.application.ports import PasswordHasher, TokenService, UnitOfWork
from taskapp.domain.user import User


@dataclass(frozen=True)
class Dependencies:
    """What the routes need from the outside world; built in the composition root."""

    uow_factory: Callable[[], UnitOfWork]
    hasher: PasswordHasher
    tokens: TokenService
    shutdown: Callable[[], Awaitable[None]] | None = None


def get_dependencies(request: Request) -> Dependencies:
    raise NotImplementedError


async def current_user(request: Request) -> User:
    raise NotImplementedError
