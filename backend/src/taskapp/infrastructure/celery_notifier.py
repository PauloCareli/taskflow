import asyncio
import logging

from taskapp.application.ports import AssignmentMessage
from taskapp.infrastructure.tasks import NotificationTask

logger = logging.getLogger("taskapp.notifications")


class CeleryNotifier:
    """`Notifier` that queues the assignment notification on the Celery broker.

    It never raises: a broker that cannot be reached is retried a few times and then logged,
    so a stored assignment is never reported to the client as a failure. Retrying is safe
    because the task is idempotent.
    """

    def __init__(
        self, task: NotificationTask, attempts: int = 3, backoff_seconds: float = 0.1
    ) -> None:
        self._task = task
        self._attempts = attempts
        self._backoff = backoff_seconds

    async def notify(self, message: AssignmentMessage) -> None:
        args = (str(message.task_id), str(message.assignee_id))
        for attempt in range(1, self._attempts + 1):
            try:
                # The broker client is synchronous; keep it off the event loop.
                await asyncio.to_thread(lambda: self._task.apply_async(args=args))
                return
            except Exception:
                if attempt == self._attempts:
                    logger.error(
                        "could not queue the notification for task %s (assignee %s) after "
                        "%d attempts",
                        message.task_id,
                        message.assignee_id,
                        attempt,
                        exc_info=True,
                    )
                    return
                logger.warning(
                    "queueing the notification for task %s failed (attempt %d of %d), retrying",
                    message.task_id,
                    attempt,
                    self._attempts,
                )
                await asyncio.sleep(self._backoff * attempt)
