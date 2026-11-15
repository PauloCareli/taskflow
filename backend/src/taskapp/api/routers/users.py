from typing import Annotated

from fastapi import APIRouter, Depends

from taskapp.api.dependencies import Dependencies, current_user, get_dependencies
from taskapp.api.schemas import ErrorResponse, UserResponse
from taskapp.application.list_users import ListUsers
from taskapp.domain.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    summary="List users",
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid bearer token"}},
)
async def list_users(
    _user: Annotated[User, Depends(current_user)],
    dependencies: Annotated[Dependencies, Depends(get_dependencies)],
) -> list[UserResponse]:
    """Every registered user, sorted by name (for choosing an assignee)."""
    users = await ListUsers(dependencies.uow_factory()).execute()
    return [UserResponse(id=u.id, email=u.email, name=u.name) for u in users]
