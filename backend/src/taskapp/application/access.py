from uuid import UUID

from taskapp.application.ports import UnitOfWork
from taskapp.domain.errors import TaskNotFound
from taskapp.domain.task import Task


async def load_visible_task(uow: UnitOfWork, actor_id: UUID, task_id: UUID) -> Task:
    """Load a task the actor can see; a hidden task is indistinguishable from a missing one."""
    task = await uow.tasks.get(task_id)
    if task is None or not task.is_visible_to(actor_id):
        raise TaskNotFound(str(task_id))
    return task
