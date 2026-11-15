from datetime import UTC, datetime
from uuid import UUID

from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task
from tests.fakes import InMemoryTaskRepository

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


async def seed_task(
    tasks: InMemoryTaskRepository,
    creator_id: UUID,
    *,
    title: str = "Task",
    assignee_id: UUID | None = None,
    due_date: datetime | None = None,
    status: TaskStatus = TaskStatus.TODO,
    created_at: datetime | None = None,
) -> Task:
    """Put a task straight into the fake repository, without commits or messages."""
    task = Task.create(
        title=title,
        description=None,
        due_date=due_date,
        creator_id=creator_id,
        assignee_id=assignee_id,
        now=created_at or NOW,
    )
    task.status = status
    await tasks.add(task)
    tasks.writes = 0
    return task
