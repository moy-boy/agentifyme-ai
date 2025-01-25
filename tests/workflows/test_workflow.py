# # pylint: disable=missing-function-docstring

# import asyncio

# import pytest

# from agentifyme.workflows import (
#     WorkflowConfig,
#     WorkflowExecutionError,
#     workflow,
# )


# def test_workflow_decorator():
#     WorkflowConfig.reset_registry()

#     @workflow
#     def greet(name: str) -> str:
#         return f"Hello, {name}!"

#     assert greet("world") == "Hello, world!"
#     assert greet("agentifyme") == "Hello, agentifyme!"
#     assert greet("python") == "Hello, python!"

#     workflow_instance = WorkflowConfig.get("greet")
#     assert workflow_instance is not None
#     assert workflow_instance("world") == "Hello, world!"
#     assert workflow_instance("agentifyme") == "Hello, agentifyme!"
#     assert workflow_instance("python") == "Hello, python!"

#     workflow_config = workflow_instance.config
#     assert workflow_config is not None
#     assert workflow_config.name == "greet"
#     assert workflow_config.description == ""


# def test_workflow_decorator_with_name_and_description():
#     WorkflowConfig.reset_registry()

#     @workflow(name="greet", description="Generate a greeting message.")
#     def greet(name: str) -> str:
#         return f"Hello, {name}!"

#     assert greet("world") == "Hello, world!"
#     assert greet("agentifyme") == "Hello, agentifyme!"
#     assert greet("python") == "Hello, python!"

#     workflow_instance = WorkflowConfig.get("greet")
#     assert workflow_instance is not None
#     assert workflow_instance("world") == "Hello, world!"
#     assert workflow_instance("agentifyme") == "Hello, agentifyme!"
#     assert workflow_instance("python") == "Hello, python!"

#     workflow_config = workflow_instance.config
#     assert workflow_config is not None
#     assert workflow_config.name == "greet"
#     assert workflow_config.description == "Generate a greeting message."


# # Synchronous workflow test
# def test_sync_workflow():
#     @workflow
#     def sync_workflow(x: int, y: int) -> int:
#         return x + y

#     result = sync_workflow(2, 3)
#     assert result == 5
#     assert sync_workflow.__agentifyme_metadata["is_async"] == False


# # Asynchronous workflow test
# @pytest.mark.asyncio
# async def test_async_workflow():
#     @workflow
#     async def async_workflow(x: int, y: int) -> int:
#         await asyncio.sleep(0.1)
#         return x + y

#     result = await async_workflow(2, 3)
#     assert result == 5
#     assert async_workflow.__agentifyme_metadata["is_async"] == True


# # Test workflow with custom name and description
# def test_workflow_custom_name_description():
#     @workflow(name="Custom Workflow", description="A custom workflow")
#     def custom_workflow():
#         return "Custom"

#     assert custom_workflow.__agentifyme_metadata["name"] == "Custom Workflow"
#     assert custom_workflow.__agentifyme_metadata["description"] == "A custom workflow"


# # Test workflow execution error
# def test_workflow_execution_error():
#     @workflow
#     def error_workflow():
#         raise ValueError("Test error")

#     with pytest.raises(WorkflowExecutionError):
#         error_workflow()


# # Test async workflow execution error
# @pytest.mark.asyncio
# async def test_async_workflow_execution_error():
#     @workflow
#     async def async_error_workflow():
#         await asyncio.sleep(0.1)
#         raise ValueError("Async test error")

#     # with pytest.raises(AsyncWorkflowExecutionError):
#     #     await async_error_workflow()
