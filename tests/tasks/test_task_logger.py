# pylint: disable=missing-function-docstring

import pytest
import structlog
from structlog.testing import LogCapture

from agentifyme.logger import get_logger
from agentifyme.tasks import Task, TaskConfig, task


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])


def test_task_logger(log_output):
    TaskConfig.reset_registry()

    logger = get_logger()

    @task
    def say_hello(name: str) -> str:
        logger.info("Saying hello", name=name)
        return f"Hello, {name}!"

    assert say_hello("world") == "Hello, world!"

    # The log_output fixture captures the log entries
    assert log_output.entries == [
        {
            "event": "Running task: say_hello",
            "log_level": "info",
        },
        {
            "event": "Saying hello",
            "log_level": "info",
            "name": "world",
        },
    ]
