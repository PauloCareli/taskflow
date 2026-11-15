import logging

from celery import Celery, Task

__all__ = ["MAX_RETRIES", "NOTIFY_ASSIGNMENT", "NotificationTask", "register_tasks"]

NotificationTask = Task[..., None]

logger = logging.getLogger("taskapp.notifications")

NOTIFY_ASSIGNMENT = "taskapp.notify_assignment"
MAX_RETRIES = 3


def deliver_assignment_message(task_id: str, assignee_id: str) -> None:
    """Deliver the assignment message. v1 only logs it (see `spec/00-overview.md`)."""
    raise NotImplementedError


def register_tasks(app: Celery) -> NotificationTask:
    """Register the background tasks on `app` and return the assignment notification task."""

    @app.task(name=NOTIFY_ASSIGNMENT, bind=True, max_retries=MAX_RETRIES)
    def notify_assignment(self: NotificationTask, task_id: str, assignee_id: str) -> None:
        raise NotImplementedError

    return notify_assignment
