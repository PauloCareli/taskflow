from collections.abc import Collection
from uuid import UUID

from sqlalchemy import ColumnElement, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taskapp.application.ports import Credentials, TaskFilters
from taskapp.domain.errors import EmailTaken
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task
from taskapp.domain.user import User
from taskapp.infrastructure.db.models import TaskModel, UserModel


def _to_task(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        title=model.title,
        description=model.description,
        status=TaskStatus(model.status),
        due_date=model.due_date,
        creator_id=model.creator_id,
        assignee_id=model.assignee_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        completed_at=model.completed_at,
    )


def _to_task_model(task: Task) -> TaskModel:
    return TaskModel(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        due_date=task.due_date,
        creator_id=task.creator_id,
        assignee_id=task.assignee_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


def _to_user(model: UserModel) -> User:
    return User(id=model.id, email=model.email, name=model.name)


def _conditions(user_id: UUID, filters: TaskFilters) -> list[ColumnElement[bool]]:
    conditions = [or_(TaskModel.creator_id == user_id, TaskModel.assignee_id == user_id)]
    if filters.statuses:
        conditions.append(TaskModel.status.in_([status.value for status in filters.statuses]))
    if filters.due_before is not None:
        conditions.append(TaskModel.due_date <= filters.due_before)
    if filters.due_after is not None:
        conditions.append(TaskModel.due_date >= filters.due_after)
    return conditions


class SqlTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: Task) -> None:
        self._session.add(_to_task_model(task))
        await self._session.flush()

    async def get(self, task_id: UUID) -> Task | None:
        model = await self._session.get(TaskModel, task_id)
        return _to_task(model) if model else None

    async def save(self, task: Task) -> None:
        await self._session.merge(_to_task_model(task))
        await self._session.flush()

    async def delete(self, task_id: UUID) -> None:
        await self._session.execute(delete(TaskModel).where(TaskModel.id == task_id))

    async def list_visible(
        self, user_id: UUID, filters: TaskFilters, *, offset: int, limit: int
    ) -> tuple[list[Task], int]:
        # A due-date bound never matches a task without a due date (NULL comparisons are false).
        conditions = _conditions(user_id, filters)
        total = await self._session.scalar(
            select(func.count()).select_from(TaskModel).where(*conditions)
        )
        rows = await self._session.scalars(
            select(TaskModel)
            .where(*conditions)
            .order_by(
                TaskModel.due_date.asc().nulls_last(), TaskModel.created_at.desc(), TaskModel.id
            )
            .offset(offset)
            .limit(limit)
        )
        return [_to_task(row) for row in rows], total or 0


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return _to_user(model) if model else None

    async def get_many(self, user_ids: Collection[UUID]) -> dict[UUID, User]:
        raise NotImplementedError

    async def list_all(self) -> list[User]:
        raise NotImplementedError

    async def get_credentials_by_email(self, email: str) -> Credentials | None:
        model = await self._session.scalar(
            select(UserModel).where(func.lower(UserModel.email) == email.lower())
        )
        return Credentials(_to_user(model), model.password_hash) if model else None

    async def add(self, user: User, password_hash: str) -> None:
        self._session.add(
            UserModel(id=user.id, email=user.email, name=user.name, password_hash=password_hash)
        )
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise EmailTaken(user.email) from error
