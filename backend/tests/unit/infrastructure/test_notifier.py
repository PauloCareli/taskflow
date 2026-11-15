import logging
from uuid import uuid4

import pytest

from taskapp.application.ports import AssignmentMessage
from taskapp.infrastructure.notifier import LoggingNotifier


async def test_ac07_an_assignment_message_is_logged_with_the_task_and_the_assignee(
    caplog: pytest.LogCaptureFixture,
) -> None:
    message = AssignmentMessage(task_id=uuid4(), assignee_id=uuid4())

    with caplog.at_level(logging.INFO, logger="taskapp.notifications"):
        await LoggingNotifier().notify(message)

    [record] = caplog.records
    assert record.name == "taskapp.notifications"
    assert str(message.task_id) in record.getMessage()
    assert str(message.assignee_id) in record.getMessage()
