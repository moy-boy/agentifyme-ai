# pylint: disable=missing-function-docstring
import pytest

from agentifyme.components.workflow import WorkflowConfig, workflow
from agentifyme.errors import AgentifyMeError, ErrorCategory


@pytest.fixture(autouse=True)
def reset_workflow_registry():
    WorkflowConfig.reset_registry()


def test_workflow_decorator():
    @workflow
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    assert greet("world") == "Hello, world!"
    assert greet("agentifyme") == "Hello, agentifyme!"
    assert greet("python") == "Hello, python!"

    workflow_instance = WorkflowConfig.get("greet")
    assert workflow_instance is not None
    assert workflow_instance("world") == "Hello, world!"
    assert workflow_instance("agentifyme") == "Hello, agentifyme!"
    assert workflow_instance("python") == "Hello, python!"

    workflow_config = workflow_instance.config
    assert workflow_config is not None
    assert workflow_config.name == "greet"
    assert workflow_config.description == ""


def test_workflow_decorator_with_name_and_description():
    @workflow(name="greet", description="Generate a greeting message.")
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    assert greet("world") == "Hello, world!"
    assert greet("agentifyme") == "Hello, agentifyme!"
    assert greet("python") == "Hello, python!"

    workflow_instance = WorkflowConfig.get("greet")
    assert workflow_instance is not None
    assert workflow_instance("world") == "Hello, world!"
    assert workflow_instance("agentifyme") == "Hello, agentifyme!"
    assert workflow_instance("python") == "Hello, python!"

    workflow_config = workflow_instance.config
    assert workflow_config is not None
    assert workflow_config.name == "greet"
    assert workflow_config.description == "Generate a greeting message."


def test_workflow_execution_error():
    @workflow
    def error_workflow():
        raise ValueError("Test error")

    with pytest.raises(AgentifyMeError) as exc_info:
        error_workflow()

    error = exc_info.value
    assert error.category == ErrorCategory.EXECUTION
    assert error.context.component_type == "workflow"
    assert "ValueError" in str(error)
    assert "Test error" in str(error)
