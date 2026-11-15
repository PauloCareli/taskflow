from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from taskapp.api.dependencies import Dependencies, current_user, get_dependencies
from taskapp.api.schemas import (
    AssignRequest,
    CreateTaskRequest,
    ErrorResponse,
    PatchTaskRequest,
    TaskListResponse,
    TaskResponse,
)
from taskapp.application.assign_task import AssignTask
from taskapp.application.complete_task import CompleteTask
from taskapp.application.create_task import CreateTask
from taskapp.application.delete_task import DeleteTask
from taskapp.application.get_task import GetTask
from taskapp.application.list_tasks import DEFAULT_PAGE_SIZE, ListTasks
from taskapp.application.ports import TaskFilters
from taskapp.application.task_views import BuildTaskViews
from taskapp.application.update_task import UpdateTask
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import UNSET, Task
from taskapp.domain.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

UserDep = Annotated[User, Depends(current_user)]
DependenciesDep = Annotated[Dependencies, Depends(get_dependencies)]

_ERRORS = {
    401: "Missing, malformed, expired or invalid bearer token",
    403: "The caller can see the task but may not do this",
    404: "The task (or user) does not exist or is not visible to the caller",
    409: "The status change is not allowed",
    422: "The request is not valid",
}


def _errors(*codes: int) -> dict[int | str, dict[str, Any]]:
    return {code: {"model": ErrorResponse, "description": _ERRORS[code]} for code in codes}


async def _present(dependencies: Dependencies, task: Task) -> TaskResponse:
    [view] = await BuildTaskViews(dependencies.uow_factory()).execute([task])
    return TaskResponse.from_view(view)


@router.get("", summary="List tasks", responses=_errors(401, 422))
async def list_tasks(
    user: UserDep,
    dependencies: DependenciesDep,
    status: Annotated[
        list[TaskStatus] | None, Query(description="Repeat to match any of several statuses")
    ] = None,
    due_before: Annotated[datetime | None, Query(description="Inclusive, timezone-aware")] = None,
    due_after: Annotated[datetime | None, Query(description="Inclusive, timezone-aware")] = None,
    page: Annotated[int, Query(description="Starts at 1")] = 1,
    size: Annotated[int, Query(description="1 to 100")] = DEFAULT_PAGE_SIZE,
) -> TaskListResponse:
    """The tasks you created or are assigned to, soonest due date first (undated last)."""
    filters = TaskFilters(
        statuses=frozenset(status or []), due_before=due_before, due_after=due_after
    )
    result = await ListTasks(dependencies.uow_factory()).execute(
        user.id, filters, page=page, size=size
    )
    views = await BuildTaskViews(dependencies.uow_factory()).execute(result.items)
    return TaskListResponse(
        items=[TaskResponse.from_view(v) for v in views],
        total=result.total,
        page=result.page,
        size=result.size,
    )


@router.post("", status_code=201, summary="Create a task", responses=_errors(401, 404, 422))
async def create_task(
    body: CreateTaskRequest, user: UserDep, dependencies: DependenciesDep
) -> TaskResponse:
    task = await CreateTask(
        dependencies.uow_factory(), dependencies.clock, dependencies.notifier
    ).execute(
        user.id,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        assignee_id=body.assignee_id,
    )
    return await _present(dependencies, task)


@router.get("/{task_id}", summary="Get a task", responses=_errors(401, 404, 422))
async def get_task(task_id: UUID, user: UserDep, dependencies: DependenciesDep) -> TaskResponse:
    task = await GetTask(dependencies.uow_factory()).execute(user.id, task_id)
    return await _present(dependencies, task)


@router.patch("/{task_id}", summary="Update a task", responses=_errors(401, 403, 404, 409, 422))
async def update_task(
    task_id: UUID, body: PatchTaskRequest, user: UserDep, dependencies: DependenciesDep
) -> TaskResponse:
    """Fields are for the creator; the status can also be changed by the assignee."""
    sent = body.model_fields_set
    task = await UpdateTask(dependencies.uow_factory(), dependencies.clock).execute(
        user.id,
        task_id,
        title=body.title if "title" in sent and body.title is not None else UNSET,
        description=body.description if "description" in sent else UNSET,
        due_date=body.due_date if "due_date" in sent else UNSET,
        status=body.status,
    )
    return await _present(dependencies, task)


@router.delete(
    "/{task_id}", status_code=204, summary="Delete a task", responses=_errors(401, 403, 404, 422)
)
async def delete_task(task_id: UUID, user: UserDep, dependencies: DependenciesDep) -> None:
    await DeleteTask(dependencies.uow_factory()).execute(user.id, task_id)


@router.post(
    "/{task_id}/assign",
    summary="Assign or unassign a task",
    responses=_errors(401, 403, 404, 422),
)
async def assign_task(
    task_id: UUID, body: AssignRequest, user: UserDep, dependencies: DependenciesDep
) -> TaskResponse:
    """Creator only. `assignee_id: null` clears the assignee."""
    task = await AssignTask(
        dependencies.uow_factory(), dependencies.clock, dependencies.notifier
    ).execute(user.id, task_id, body.assignee_id)
    return await _present(dependencies, task)


@router.post(
    "/{task_id}/complete", summary="Complete a task", responses=_errors(401, 404, 409, 422)
)
async def complete_task(
    task_id: UUID, user: UserDep, dependencies: DependenciesDep
) -> TaskResponse:
    """The creator or the assignee can complete a task."""
    task = await CompleteTask(dependencies.uow_factory(), dependencies.clock).execute(
        user.id, task_id
    )
    return await _present(dependencies, task)
