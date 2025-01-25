# pylint: disable=missing-function-docstring

import asyncio

import pytest

from agentifyme.components.utils import InvalidNameError
from agentifyme.components.workflow import WorkflowConfig, workflow
from agentifyme.errors import ErrorCategory


@pytest.fixture(autouse=True)
def reset_workflow_registry():
    WorkflowConfig.reset_registry()


@pytest.mark.asyncio
async def test_async_workflow_decorator():
    @workflow
    async def async_greet(name: str) -> str:
        await asyncio.sleep(0.1)  # Simulate async operation
        return f"Hello, {name}!"

    assert await async_greet("world") == "Hello, world!"
    assert await async_greet("agentifyme") == "Hello, agentifyme!"
    assert await async_greet("python") == "Hello, python!"

    workflow_instance = WorkflowConfig.get("async_greet")
    assert workflow_instance is not None
    assert await workflow_instance("world") == "Hello, world!"
    assert await workflow_instance("agentifyme") == "Hello, agentifyme!"
    assert await workflow_instance("python") == "Hello, python!"

    workflow_config = workflow_instance.config
    assert workflow_config is not None
    assert workflow_config.name == "async_greet"
    assert workflow_config.description == ""


@pytest.mark.asyncio
async def test_workflow_decorator_with_name_and_description():
    @workflow(name="greet", description="Generate a greeting message.")
    async def greet(name: str) -> str:
        await asyncio.sleep(0.1)  # Simulate async operation
        return f"Hello, {name}!"

    assert await greet("world") == "Hello, world!"
    assert await greet("agentifyme") == "Hello, agentifyme!"
    assert await greet("python") == "Hello, python!"

    workflow_instance = WorkflowConfig.get("greet")
    assert workflow_instance is not None
    assert await workflow_instance("world") == "Hello, world!"
    assert await workflow_instance("agentifyme") == "Hello, agentifyme!"
    assert await workflow_instance("python") == "Hello, python!"

    workflow_config = workflow_instance.config
    assert workflow_config is not None
    assert workflow_config.name == "greet"
    assert workflow_config.description == "Generate a greeting message."


@pytest.mark.asyncio
async def test_workflow_custom_name_description():
    @workflow(name="Invalid Workflow Name", description="A custom workflow")
    async def custom_workflow():
        return "Invalid Workflow Name"

    with pytest.raises(InvalidNameError) as exc_info:
        await custom_workflow()

    error = exc_info.value
    assert error.error_code == "INVALID_NAME"
    assert error.category == ErrorCategory.VALIDATION
    assert error.context.component_type == "workflow"
    assert error.context.component_id == "name_validation"
    print(error)
    assert "Invalid Workflow Name" in str(error)
