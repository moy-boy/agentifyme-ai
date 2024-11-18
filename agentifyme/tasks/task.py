import asyncio
from typing import Any, Callable, Optional, overload

from loguru import logger

from agentifyme.config import BaseModule, TaskConfig
from agentifyme.utilities.func_utils import (
    execute_function,
    get_function_metadata,
)


class TaskError(Exception):
    pass


class TaskExecutionError(TaskError):
    pass


class AsyncTaskExecutionError(TaskError):
    pass


class Task(BaseModule):
    def __init__(self, config: TaskConfig, *args, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.config = config

    def run(self, *args, **kwargs: Any) -> Any:
        logger.info(f"Running task: {self.config.name}")
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            try:
                return execute_function(self.config.func, kwargs)
            except Exception as e:
                raise TaskExecutionError(
                    f"Error executing task {self.config.name}: {str(e)}"
                ) from e
        else:
            raise NotImplementedError("Task function not implemented")

    async def arun(self, *args, **kwargs: Any) -> Any:
        logger.info(f"Running async task: {self.config.name}")
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            try:
                if asyncio.iscoroutinefunction(self.config.func):
                    return await self.config.func(**kwargs)
                else:
                    return await asyncio.to_thread(self.config.func, **kwargs)
            except Exception as e:
                raise AsyncTaskExecutionError(
                    f"Error executing async task {self.config.name}: {str(e)}"
                ) from e
        else:
            raise NotImplementedError("Task function not implemented")


@overload
def task(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator function for defining a workflow."""


@overload
def task(*, name: str, description: Optional[str] = None) -> Callable[..., Any]: ...


def task(
    func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    objective: Optional[str] = None,
    instructions: Optional[str] = None,
    # tools: Optional[list[Tool]] = None,
) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func_metadata = get_function_metadata(func)
        task_config = TaskConfig(
            name=func_metadata.name,
            description=description or func_metadata.description,
            input_parameters=func_metadata.input_parameters,
            output_parameters=func_metadata.output_parameters,
            objective=objective,
            instructions=instructions,
            func=func,
            # tools=tools,
        )

        _task_instance = Task(task_config)
        TaskConfig.register(_task_instance)

        def wrapper(*args, **kwargs) -> Any:
            kwargs.update(zip(func.__code__.co_varnames, args))
            result = _task_instance(**kwargs)
            return result

        # Add visualization metadata
        wrapper.__agentifyme = _task_instance  # type: ignore
        wrapper.__agentifyme_metadata = {  # type: ignore
            "type": "task",
            "name": task_config.name,
            "description": task_config.description,
            "objective": task_config.objective,
            "instructions": task_config.instructions,
            "input_parameters": {
                name: param.name for name, param in task_config.input_parameters.items()
            },
            "output_parameters": [
                param.name for param in task_config.output_parameters
            ],
        }

        # pylint: enable=protected-access

        return wrapper

    if callable(func):
        return decorator(func)
    elif name is not None:

        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            return decorator(func)

        return decorator
    else:
        raise TaskError("Invalid arguments for workflow decorator")
