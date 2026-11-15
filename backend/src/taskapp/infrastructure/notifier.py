import logging

from taskapp.application.ports import AssignmentMessage

logger = logging.getLogger("taskapp.notifications")


class LoggingNotifier:
    """Placeholder `Notifier`: records the assignment message in the log and nothing else."""

    async def notify(self, message: AssignmentMessage) -> None:
        logger.info("task %s assigned to user %s", message.task_id, message.assignee_id)
