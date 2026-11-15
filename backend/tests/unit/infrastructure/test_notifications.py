import logging
import time
from typing import Any
from uuid import uuid4

import pytest
from celery import Celery

from taskapp.application.ports import AssignmentMessage
from taskapp.infrastructure import tasks as tasks_module
from taskapp.infrastructure.celery_app import create_celery_app
from taskapp.infrastructure.celery_notifier import CeleryNotifier
from taskapp.infrastructure.settings import Settings
from taskapp.infrastructure.tasks import MAX_RETRIES, register_tasks

SECRET = "unit-test-secret-that-is-long-enough-for-hs256"
UNREACHABLE = "redis://127.0.0.1:1/0"
LOGGER = "taskapp.notifications"


def eager_app() -> Celery:
    return create_celery_app(Settings(jwt_secret=SECRET, celery_eager=True, redis_url=UNREACHABLE))  # type: ignore[arg-type]


def records(caplog: pytest.LogCaptureFixture, level: int = logging.INFO) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == LOGGER and r.levelno == level]


def message() -> AssignmentMessage:
    return AssignmentMessage(task_id=uuid4(), assignee_id=uuid4())


def test_ac04_the_task_logs_one_line_naming_the_task_and_the_assignee(
    caplog: pytest.LogCaptureFixture,
) -> None:
    task = register_tasks(eager_app())
    msg = message()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        task.apply(args=(str(msg.task_id), str(msg.assignee_id)))

    [record] = records(caplog)
    assert str(msg.task_id) in record.getMessage()
    assert str(msg.assignee_id) in record.getMessage()


def test_ac04_running_the_task_again_gives_the_same_outcome(
    caplog: pytest.LogCaptureFixture,
) -> None:
    task = register_tasks(eager_app())
    msg = message()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        first = task.apply(args=(str(msg.task_id), str(msg.assignee_id)))
        second = task.apply(args=(str(msg.task_id), str(msg.assignee_id)))

    assert first.result == second.result
    assert first.successful() and second.successful()
    lines = [r.getMessage() for r in records(caplog)]
    assert len(lines) == 2
    assert lines[0] == lines[1]


def test_ac04_a_failing_delivery_fails_the_task_so_that_the_worker_can_retry_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = register_tasks(eager_app())

    def broken(task_id: str, assignee_id: str) -> None:
        raise ConnectionError("down")

    monkeypatch.setattr(tasks_module, "deliver_assignment_message", broken)

    with pytest.raises(ConnectionError):
        task(str(uuid4()), str(uuid4()))


def test_ac04_the_worker_retries_a_bounded_number_of_times_with_a_growing_delay() -> None:
    task = register_tasks(eager_app())

    assert task.autoretry_for == (Exception,)  # type: ignore[attr-defined]
    assert task.max_retries == MAX_RETRIES
    assert task.retry_backoff is not False  # type: ignore[attr-defined]
    assert 0 < task.retry_backoff_max <= 60  # type: ignore[attr-defined]


def test_ac04_giving_up_logs_the_error_once_naming_the_task_and_the_assignee(
    caplog: pytest.LogCaptureFixture,
) -> None:
    task = register_tasks(eager_app())
    msg = message()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        task.on_failure(
            ConnectionError("down"),
            "celery-id",
            (str(msg.task_id), str(msg.assignee_id)),
            {},
            None,  # type: ignore[arg-type]
        )

    [error] = records(caplog, logging.ERROR)
    assert str(msg.task_id) in error.getMessage()
    assert str(msg.assignee_id) in error.getMessage()


async def test_ac03_notifying_runs_the_notification_task_once_with_both_ids(
    caplog: pytest.LogCaptureFixture,
) -> None:
    notifier = CeleryNotifier(register_tasks(eager_app()))
    msg = message()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await notifier.notify(msg)

    [record] = records(caplog)
    assert str(msg.task_id) in record.getMessage()
    assert str(msg.assignee_id) in record.getMessage()


class FlakyTask:
    """Stands in for a Celery task whose broker fails a given number of times."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls: list[dict[str, Any]] = []

    def apply_async(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if len(self.calls) <= self.failures:
            raise ConnectionError("broker down")


async def test_ac05_a_temporary_broker_failure_is_retried_and_not_logged_as_an_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    task = FlakyTask(failures=2)
    notifier = CeleryNotifier(task, backoff_seconds=0)  # type: ignore[arg-type]

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await notifier.notify(message())

    assert len(task.calls) == 3
    assert records(caplog, logging.ERROR) == []


async def test_ac05_a_broker_that_stays_down_is_retried_a_bounded_number_of_times_then_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    task = FlakyTask(failures=99)
    notifier = CeleryNotifier(task, attempts=3, backoff_seconds=0)  # type: ignore[arg-type]
    msg = message()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await notifier.notify(msg)  # does not raise

    assert len(task.calls) == 3
    [error] = records(caplog, logging.ERROR)
    assert str(msg.task_id) in error.getMessage()


async def test_ac05_an_unreachable_redis_gives_up_quickly_without_raising(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_celery_app(Settings(jwt_secret=SECRET, redis_url=UNREACHABLE))  # type: ignore[arg-type]
    task = register_tasks(app)
    started = time.monotonic()

    with caplog.at_level(logging.INFO, logger=LOGGER):
        await CeleryNotifier(task).notify(message())

    assert time.monotonic() - started < 5
    assert len(records(caplog, logging.ERROR)) == 1
