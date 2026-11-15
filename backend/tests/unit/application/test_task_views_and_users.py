import pytest

from taskapp.application.list_tasks import ListTasks
from taskapp.application.list_users import ListUsers
from taskapp.application.task_views import BuildTaskViews
from taskapp.domain.errors import ValidationError
from taskapp.domain.user import User
from tests.fakes import InMemoryTaskRepository, InMemoryUnitOfWork, InMemoryUserRepository
from tests.unit.application.helpers import seed_task


async def test_ac02_task_views_carry_the_creator_and_the_assignee(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User, bob: User
) -> None:
    assigned = await seed_task(tasks, alice.id, title="assigned", assignee_id=bob.id)
    unassigned = await seed_task(tasks, alice.id, title="unassigned")

    views = await BuildTaskViews(uow).execute([assigned, unassigned])

    assert [(v.task, v.creator, v.assignee) for v in views] == [
        (assigned, alice, bob),
        (unassigned, alice, None),
    ]


async def test_ac04_task_views_look_users_up_once_however_many_tasks(
    uow: InMemoryUnitOfWork,
    users: InMemoryUserRepository,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
) -> None:
    many = [await seed_task(tasks, alice.id, assignee_id=bob.id) for _ in range(30)]

    views = await BuildTaskViews(uow).execute(many)

    assert len(views) == 30
    assert users.get_many_calls == 1


async def test_ac04_no_tasks_means_no_views_and_no_lookup(
    uow: InMemoryUnitOfWork, users: InMemoryUserRepository
) -> None:
    assert await BuildTaskViews(uow).execute([]) == []
    assert users.get_many_calls == 0


async def test_ac08_users_are_listed_sorted_by_name(
    uow: InMemoryUnitOfWork, alice: User, bob: User, carol: User
) -> None:
    assert await ListUsers(uow).execute() == [alice, bob, carol]


async def test_ac04_an_oversized_page_is_refused_with_a_message_naming_the_maximum(
    uow: InMemoryUnitOfWork, alice: User
) -> None:
    with pytest.raises(ValidationError, match="maximum size is 100"):
        await ListTasks(uow).execute(alice.id, size=101)
