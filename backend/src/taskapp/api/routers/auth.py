from typing import Annotated

from fastapi import APIRouter, Depends

from taskapp.api.dependencies import Dependencies, current_user, get_dependencies
from taskapp.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from taskapp.application.login_user import LoginUser
from taskapp.application.register_user import RegisterUser
from taskapp.domain.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

DependenciesDep = Annotated[Dependencies, Depends(get_dependencies)]


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, dependencies: DependenciesDep) -> UserResponse:
    user = await RegisterUser(dependencies.uow_factory(), dependencies.hasher).execute(
        email=body.email, name=body.name, password=body.password
    )
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/login")
async def login(body: LoginRequest, dependencies: DependenciesDep) -> TokenResponse:
    token = await LoginUser(
        dependencies.uow_factory(), dependencies.hasher, dependencies.tokens
    ).execute(email=body.email, password=body.password)
    return TokenResponse(access_token=token.token, expires_in=token.expires_in)


@router.get("/me")
async def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name)
