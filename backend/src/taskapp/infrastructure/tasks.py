import logging
from typing import Any

from celery import Celery, Task

__all__ = ["MAX_RETRIES", "NOTIFY_ASSIGNMENT", "NotificationTask", "register_tasks"]

NotificationTask = Task[..., None]

logger = logging.getLogger("taskapp.notifications")

NOTIFY_ASSIGNMENT = "taskapp.notify_assignment"
MAX_RETRIES = 3
_MAX_RETRY_DELAY_SECONDS = 30


def deliver_assignment_message(task_id: str, assignee_id: str) -> None:
    """Deliver the assignment message. v1 only logs it (see `spec/00-overview.md`)."""
    logger.info("task %s assigned to user %s", task_id, assignee_id)


class _LogsFinalFailure(Task):  # type: ignore[type-arg]
    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """Called by the worker once the retries are used up."""
        logger.error("giving up on notifying user %s about task %s", args[1], args[0], exc_info=exc)


def register_tasks(app: Celery) -> NotificationTask:
    """Register the background tasks on `app` and return the assignment notification task."""

    @app.task(
        name=NOTIFY_ASSIGNMENT,
        base=_LogsFinalFailure,
        autoretry_for=(Exception,),
        max_retries=MAX_RETRIES,
        retry_backoff=2,
        retry_backoff_max=_MAX_RETRY_DELAY_SECONDS,
    )
    def notify_assignment(task_id: str, assignee_id: str) -> None:
        """Idempotent: it keeps no state, so a retry or a duplicate only repeats the log line."""
        deliver_assignment_message(task_id, assignee_id)

    return notify_assignment
