from taskapp.application.ports import AssignmentMessage


class LoggingNotifier:
    """Placeholder `Notifier`: records the assignment message in the log and nothing else."""

    async def notify(self, message: AssignmentMessage) -> None:
        raise NotImplementedError
