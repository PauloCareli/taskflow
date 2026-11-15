from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from taskapp.api.dependencies import Dependencies, current_user, get_dependencies
from taskapp.api.schemas import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from taskapp.application.login_user import LoginUser
from taskapp.application.register_user import RegisterUser
from taskapp.domain.user import User

DependenciesDep = Annotated[Dependencies, Depends(get_dependencies)]


# `request` is only here for the rate limiter, which finds the client through it.
async def register(
    request: Request, body: RegisterRequest, dependencies: DependenciesDep
) -> UserResponse:
    user = await RegisterUser(dependencies.uow_factory(), dependencies.hasher).execute(
        email=body.email, name=body.name, password=body.password
    )
    return UserResponse(id=user.id, email=user.email, name=user.name)


async def login(
    request: Request, body: LoginRequest, dependencies: DependenciesDep
) -> TokenResponse:
    token = await LoginUser(
        dependencies.uow_factory(), dependencies.hasher, dependencies.tokens
    ).execute(email=body.email, password=body.password)
    return TokenResponse(access_token=token.token, expires_in=token.expires_in)


async def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name)


def build_router(limiter: Limiter | None = None, auth_limit: str | None = None) -> APIRouter:
    """The auth routes; login and register get the stricter per-address limit when configured."""

    def limited(endpoint: Callable[..., Any]) -> Callable[..., Any]:
        if limiter is None or auth_limit is None:
            return endpoint
        limited_endpoint: Callable[..., Any] = limiter.limit(
            auth_limit, key_func=get_remote_address
        )(endpoint)
        return limited_endpoint

    rate_limited: dict[int | str, dict[str, Any]] = {
        429: {"model": ErrorResponse, "description": "Too many requests"}
    }
    router = APIRouter(prefix="/auth", tags=["auth"])
    router.post("/register", status_code=201, responses=rate_limited)(limited(register))
    router.post("/login", responses=rate_limited)(limited(login))
    router.get("/me")(me)
    return router
