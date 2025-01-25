import asyncio

import pytest

from agentifyme.components.utils import Param
from agentifyme.components.workflow import WorkflowConfig, workflow


def dummy_func():
    pass


async def async_dummy_func():
    await asyncio.sleep(0.1)


def create_valid_config(**kwargs):
    default_config = {
        "name": "Test Workflow",
        "slug": "test-workflow",
        "func": dummy_func,
        "input_parameters": {"param1": Param(name="param1", data_type="int", description="A parameter")},
        "output_parameters": [Param(name="output1", data_type="str", description="An output parameter")],
        "schedule": "* * * * *",  # Default schedule
    }
    default_config.update(kwargs)
    return WorkflowConfig(**default_config)


# def test_valid_timedelta_schedules():
#     cases = [
#         (timedelta(minutes=1), "* * * * *"),
#         (timedelta(minutes=30), "*/30 * * * *"),
#         (timedelta(hours=1), "0 * * * *"),
#         (timedelta(hours=2), "0 */2 * * *"),
#         (timedelta(hours=3), "0 */3 * * *"),
#         (timedelta(hours=4), "0 */4 * * *"),
#         (timedelta(hours=6), "0 */6 * * *"),
#         (timedelta(hours=12), "0 */12 * * *"),
#         (timedelta(days=1), "0 0 * * *"),
#         (timedelta(days=7), "0 0 * * 0"),
#     ]

#     for td, expected_cron in cases:
#         config = create_valid_config(schedule=td)
#         assert config.schedule == expected_cron, f"Failed for timedelta: {td}"


def test_valid_cron_schedules():
    valid_cron_strings = [
        "* * * * *",
        "0 * * * *",
        "*/15 * * * *",
        "0 0 * * *",
        "0 0 * * 0",
    ]

    for cron_string in valid_cron_strings:
        config = create_valid_config(schedule=cron_string)
        assert config.schedule == cron_string, f"Failed for cron string: {cron_string}"


def test_invalid_cron_string():
    config = create_valid_config(schedule="invalid cron")
    assert config.schedule == "invalid cron", "Invalid cron string should be kept as is"


def test_none_schedule():
    config = create_valid_config(schedule=None)
    assert config.schedule is None


def test_empty_string_schedule():
    config = create_valid_config(schedule="")
    assert config.schedule == "", "Empty string should be kept as is"


# @pytest.mark.parametrize(
#     "invalid_type",
#     [
#         42,
#         3.14,
#         [],
#         {},
#         set(),
#     ],
# )
# def test_invalid_schedule_types(invalid_type):
#     with pytest.raises(ValidationError):
#         create_valid_config(schedule=invalid_type)


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


# def test_workflow_not_implemented():
#     workflow_config = create_valid_config(name="Empty Workflow", func=None)
#     empty_workflow = Workflow(workflow_config)

#     with pytest.raises(NotImplementedError):
#         empty_workflow.run()


# @pytest.mark.asyncio
# async def test_async_workflow_not_implemented():
#     workflow_config = create_valid_config(name="Empty Async Workflow", func=None)
#     empty_workflow = Workflow(workflow_config)

#     with pytest.raises(NotImplementedError):
#         await empty_workflow.arun()


# # Test workflow registration
# def test_workflow_registration():
#     @workflow
#     def registered_workflow():
#         pass

#     assert WorkflowConfig.get("registered_workflow") is not None


# # Test invalid workflow decorator usage
# def test_invalid_workflow_decorator():
#     with pytest.raises(TypeError):

#         @workflow(name="Invalid Workflow", invalid_arg=True)
#         def invalid_workflow():
#             pass


# @pytest.mark.asyncio
# async def test_async_workflow_run():
#     @workflow
#     async def async_workflow():
#         await asyncio.sleep(0.1)
#         return "Async result"

#     workflow_instance = async_workflow.__agentifyme
#     result = await workflow_instance.arun()
#     assert result == "Async result"


# @pytest.mark.asyncio
# async def test_sync_workflow_async_run():
#     @workflow
#     def sync_workflow():
#         return "Sync result"

#     workflow_instance = sync_workflow.__agentifyme
#     result = await workflow_instance.arun()
#     assert result == "Sync result"


@pytest.mark.asyncio
async def test_async_workflow_concurrent_execution():
    @workflow
    async def async_workflow(delay: float):
        await asyncio.sleep(delay)
        return f"Completed after {delay}s"

    workflow_instance = async_workflow.__agentifyme
    tasks = [workflow_instance.arun(0.1), workflow_instance.arun(0.2)]
    results = await asyncio.gather(*tasks)
    assert results == ["Completed after 0.1s", "Completed after 0.2s"]


@pytest.mark.asyncio
async def test_async_workflow_timeout():
    @workflow
    async def slow_workflow():
        await asyncio.sleep(1)
        return "Slow result"

    workflow_instance = slow_workflow.__agentifyme
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(workflow_instance.arun(), timeout=0.5)


@pytest.mark.asyncio
async def test_async_workflow_cancellation():
    cancel_event = asyncio.Event()

    @workflow
    async def cancellable_workflow():
        try:
            while not cancel_event.is_set():
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            return "Cancelled"
        return "Completed"

    workflow_instance = cancellable_workflow.__agentifyme
    task = asyncio.create_task(workflow_instance.arun())
    await asyncio.sleep(0.2)
    task.cancel()
    result = await task
    assert result == "Cancelled"
