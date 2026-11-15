from datetime import timedelta

import pytest

from taskapp.application.list_tasks import ListTasks
from taskapp.application.ports import TaskFilters
from taskapp.domain.errors import ValidationError
from taskapp.domain.status import TaskStatus
from taskapp.domain.task import Task
from taskapp.domain.user import User
from tests.fakes import InMemoryTaskRepository, InMemoryUnitOfWork
from tests.unit.application.helpers import NOW, seed_task


def titles(items: list[Task]) -> list[str]:
    return [t.title for t in items]


async def test_ac08_lists_only_tasks_the_caller_created_or_is_assigned_to(
    uow: InMemoryUnitOfWork,
    tasks: InMemoryTaskRepository,
    alice: User,
    bob: User,
    carol: User,
) -> None:
    await seed_task(tasks, alice.id, title="mine")
    await seed_task(tasks, bob.id, title="assigned to me", assignee_id=alice.id)
    await seed_task(tasks, bob.id, title="not mine")
    await seed_task(tasks, carol.id, title="also not mine", assignee_id=bob.id)

    result = await ListTasks(uow).execute(alice.id)

    assert sorted(titles(result.items)) == ["assigned to me", "mine"]
    assert (result.total, result.page, result.size) == (2, 1, 25)


async def test_ac08_filters_by_one_or_several_statuses(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    await seed_task(tasks, alice.id, title="todo")
    await seed_task(tasks, alice.id, title="doing", status=TaskStatus.IN_PROGRESS)
    await seed_task(tasks, alice.id, title="done", status=TaskStatus.COMPLETED)

    one = await ListTasks(uow).execute(alice.id, TaskFilters(statuses=frozenset({TaskStatus.TODO})))
    several = await ListTasks(uow).execute(
        alice.id, TaskFilters(statuses=frozenset({TaskStatus.TODO, TaskStatus.COMPLETED}))
    )

    assert titles(one.items) == ["todo"]
    assert sorted(titles(several.items)) == ["done", "todo"]


async def test_ac08_due_date_bounds_are_inclusive_and_exclude_tasks_without_a_due_date(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    for days in (1, 2, 3, 4):
        await seed_task(tasks, alice.id, title=f"d{days}", due_date=NOW + timedelta(days=days))
    await seed_task(tasks, alice.id, title="no due date")

    window = await ListTasks(uow).execute(
        alice.id,
        TaskFilters(due_after=NOW + timedelta(days=2), due_before=NOW + timedelta(days=3)),
    )
    only_before = await ListTasks(uow).execute(
        alice.id, TaskFilters(due_before=NOW + timedelta(days=1))
    )
    unfiltered = await ListTasks(uow).execute(alice.id)

    assert titles(window.items) == ["d2", "d3"]
    assert titles(only_before.items) == ["d1"]
    assert unfiltered.total == 5


async def test_ac08_filters_combine_and_never_widen_visibility(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User, bob: User
) -> None:
    due = NOW + timedelta(days=1)
    await seed_task(tasks, alice.id, title="match", due_date=due)
    await seed_task(tasks, alice.id, title="wrong status", due_date=due, status=TaskStatus.BLOCKED)
    await seed_task(tasks, bob.id, title="not visible", due_date=due)

    result = await ListTasks(uow).execute(
        alice.id, TaskFilters(statuses=frozenset({TaskStatus.TODO}), due_before=due)
    )

    assert titles(result.items) == ["match"]


async def test_ac08_sorts_by_due_date_then_newest_first_with_no_due_date_last(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    await seed_task(tasks, alice.id, title="no due, old", created_at=NOW)
    await seed_task(tasks, alice.id, title="no due, new", created_at=NOW + timedelta(hours=2))
    await seed_task(
        tasks, alice.id, title="later", due_date=NOW + timedelta(days=5), created_at=NOW
    )
    await seed_task(
        tasks, alice.id, title="soon, old", due_date=NOW + timedelta(days=1), created_at=NOW
    )
    await seed_task(
        tasks,
        alice.id,
        title="soon, new",
        due_date=NOW + timedelta(days=1),
        created_at=NOW + timedelta(hours=1),
    )

    result = await ListTasks(uow).execute(alice.id)

    assert titles(result.items) == [
        "soon, new",
        "soon, old",
        "later",
        "no due, new",
        "no due, old",
    ]


async def test_ac08_default_page_size_is_25(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    for i in range(30):
        await seed_task(tasks, alice.id, title=f"t{i}")

    result = await ListTasks(uow).execute(alice.id)

    assert len(result.items) == 25
    assert (result.total, result.page, result.size) == (30, 1, 25)


async def test_ac08_pages_do_not_overlap_and_a_page_past_the_end_is_empty(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    for i in range(5):
        await seed_task(tasks, alice.id, title=f"t{i}", created_at=NOW + timedelta(minutes=i))

    first = await ListTasks(uow).execute(alice.id, page=1, size=2)
    second = await ListTasks(uow).execute(alice.id, page=2, size=2)
    third = await ListTasks(uow).execute(alice.id, page=3, size=2)
    beyond = await ListTasks(uow).execute(alice.id, page=4, size=2)

    assert titles(first.items) + titles(second.items) + titles(third.items) == [
        "t4",
        "t3",
        "t2",
        "t1",
        "t0",
    ]
    assert beyond.items == []
    assert (beyond.total, beyond.page, beyond.size) == (5, 4, 2)


async def test_ac08_size_of_100_is_accepted(
    uow: InMemoryUnitOfWork, tasks: InMemoryTaskRepository, alice: User
) -> None:
    result = await ListTasks(uow).execute(alice.id, size=100)

    assert result.size == 100


@pytest.mark.parametrize(("page", "size"), [(0, 25), (-1, 25), (1, 0), (1, 101)])
async def test_ac08_invalid_page_or_size_is_a_validation_error(
    uow: InMemoryUnitOfWork, alice: User, page: int, size: int
) -> None:
    with pytest.raises(ValidationError):
        await ListTasks(uow).execute(alice.id, page=page, size=size)
