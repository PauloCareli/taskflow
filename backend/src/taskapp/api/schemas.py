import re
from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator

from taskapp.application.task_views import TaskView
from taskapp.domain.status import TaskStatus

_NUMBER = re.compile(r"[+-]?\d+(\.\d+)?")


def _not_a_number(value: object) -> object:
    """Dates are ISO 8601 text; a bare number (a Unix timestamp) is not accepted."""
    if isinstance(value, int | float) or (isinstance(value, str) and _NUMBER.fullmatch(value)):
        raise ValueError("must be an ISO 8601 date and time, for example 2026-01-31T09:00:00Z")
    return value


IsoDatetime = Annotated[datetime, BeforeValidator(_not_a_number)]


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 (OAuth token type, not a password)
    expires_in: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[object]


class ErrorResponse(BaseModel):
    """The uniform error body used by every endpoint."""

    error: ErrorBody


class PersonSummary(BaseModel):
    id: UUID
    name: str


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    creator: PersonSummary
    assignee: PersonSummary | None

    @classmethod
    def from_view(cls, view: TaskView) -> Self:
        task = view.task
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            creator=PersonSummary(id=view.creator.id, name=view.creator.name),
            assignee=(
                PersonSummary(id=view.assignee.id, name=view.assignee.name)
                if view.assignee
                else None
            ),
        )


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    size: int


class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    due_date: IsoDatetime | None = None
    assignee_id: UUID | None = None


class PatchTaskRequest(BaseModel):
    """Only the fields that are sent change; `null` clears description and due date."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    due_date: IsoDatetime | None = None
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def _title_and_status_cannot_be_null(self) -> Self:
        for name in ("title", "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class AssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignee_id: UUID | None
