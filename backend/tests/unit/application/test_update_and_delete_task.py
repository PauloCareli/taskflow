from datetime import timedelta
from uuid import uuid4

import pytest

from taskapp.application.delete_task import DeleteTask
from taskapp.application.update_task import UpdateTask
from taskapp.domain.errors import PermissionDenied, TaskNotFound, ValidationError
from taskapp.domain.status import TaskStatus
from taskapp.domain.user import User
from tests.fakes import FixedClock, InMemoryTaskRepository, InMemoryUnitOfWork
from tests.unit.application.helpers import seed_task


async def test_ac02_creator_updates_title_description_and_due_date(
    uow: InMemoryUnitOfWork, clock: FixedClock, tasks: InMemoryTaskRepository, alice: User
) -> None:
    task = await seed_task(tasks, alice.id)
    clock.set(clock.now() + timedelta(hours=1))
    new_due = clock.now() - timedelta(days=1)

    updated = await UpdateTask(uow, clock).execute(
        alice.id, task.id, title="New", description="more", due_date=new_due
    )

    stored = await tasks.get(task.id)
    assert stored == updated
    assert stored is not None
    assert (stored.title, stored.description, stored.due_date) == ("New", "more", new_due)
    assert stored.updated_at == clock.now()
    assert uow.commits == 1


async def test_ac02_update_with_invalid_input_changes_and_commits_nothing(
    uow: InMemoryUnitOfWork, clock: FixedClock, tasks: InMemoryTaskRepository, alice: User
) -> None:
    task = await seed_task(tasks, alice.id, title="Keep me")

    with pytest.raises(ValidationError):
        await UpdateTask(uow, clock).execute(alice.id, task.id, title="x" * 121)

    assert await tasks.get(task.id) == task
    assert uow.commits == 0


async def test_ac02_creator_can_still_update_a_completed_task(
    uow: InMemoryUnitOfWork, clock: FixedClock, tasks: InMemoryTaskRepository, alice: User
) -> None:
    task = await seed_task(tasks, alice.id, status=TaskStatus.COMPLETED)

    updated = await UpdateTask(uow, clock).execute(alice.id, task.id, title="Renamed")

    assert updated.title == "Renamed"
    assert updated.status is TaskStatus.COMPLETED


async def test_ac05_assignee_cannot_update_or_delete_the_task(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    task = await seed_task(tasks, alice.id, assignee_id=bob.id)

    with pytest.raises(PermissionDenied):
        await UpdateTask(uow, clock).execute(bob.id, task.id, title="Mine now")
    with pytest.raises(PermissionDenied):
        await DeleteTask(uow).execute(bob.id, task.id)

    assert await tasks.get(task.id) == task
    assert uow.commits == 0


async def test_ac06_update_and_delete_treat_an_invisible_task_as_missing(
    uow: InMemoryUnitOfWork,
    clock: FixedClock,
    tasks: InMemoryTaskRepository,
    alice: User,
    carol: User,
) -> None:
    task = await seed_task(tasks, alice.id)

    for task_id, actor in [(task.id, carol.id), (uuid4(), alice.id)]:
        with pytest.raises(TaskNotFound):
            await UpdateTask(uow, clock).execute(actor, task_id, title="x")
        with pytest.raises(TaskNotFound):
            await DeleteTask(uow).execute(actor, task_id)

    assert await tasks.get(task.id) == task
    assert uow.commits == 0


async def test_ac05_creator_deletes_the_task(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    task = await seed_task(tasks, alice.id)

    await DeleteTask(uow).execute(alice.id, task.id)

    assert await tasks.get(task.id) is None
    assert uow.commits == 1
