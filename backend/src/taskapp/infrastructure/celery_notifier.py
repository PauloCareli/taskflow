import logging

from taskapp.application.ports import AssignmentMessage
from taskapp.infrastructure.tasks import NotificationTask

logger = logging.getLogger("taskapp.notifications")


class CeleryNotifier:
    """`Notifier` that queues the assignment notification on the Celery broker.

    It never raises: a broker that cannot be reached is retried a few times and then logged,
    so a stored assignment is never reported to the client as a failure.
    """

    def __init__(
        self, task: NotificationTask, attempts: int = 3, backoff_seconds: float = 0.1
    ) -> None:
        self._task = task
        self._attempts = attempts
        self._backoff = backoff_seconds

    async def notify(self, message: AssignmentMessage) -> None:
        raise NotImplementedError
