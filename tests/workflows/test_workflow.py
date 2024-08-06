# pylint: disable=missing-function-docstring

from agentifyme import workflow
from agentifyme.workflows import WorkflowConfig


def test_workflow_decorator():
    WorkflowConfig.reset_registry()

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
    WorkflowConfig.reset_registry()

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
