import pytest

from agentifyme.logger import BaseLogger


@pytest.fixture(scope="session", autouse=True)
def config():
    # Initialize your configuration here
    BaseLogger.configure()
