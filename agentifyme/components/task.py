import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import wrapt

from agentifyme.components.base import BaseConfig, RunnableComponent
from agentifyme.errors import AgentifyMeValidationError, ErrorCategory, ErrorContext

from .utils import Param, get_function_metadata, validate_component_name


@dataclass
class TaskConfig(BaseConfig):
    """Represents a task configuration.

    Attributes:
        name (str): The name of the task
        slug (str): The slug of the task
        description (Optional[str]): The description of the task
        func (Callable[..., Any]): The function associated with the task
        input_parameters (dict[str, Param]): Input parameters for the task
        output_parameters (list[Param]): Output parameters for the task

    """

    input_parameters: dict[str, Param] = field(default_factory=dict)
    output_parameters: list[Param] = field(default_factory=list)


class Task(RunnableComponent):
    """A task component that can be run independently or as part of a workflow."""

    component_type: str = "task"
    config: TaskConfig

    def __init__(self, config: TaskConfig, **kwargs) -> None:
        super().__init__(component_type=self.component_type, config=config)
        self.config = config
        self._result = None

    def _validate_task(self) -> None:
        """Validate that the task function is implemented."""
        if not self.config.func:
            raise AgentifyMeValidationError(
                message="Task function not implemented",
                error_code="TASK_FUNCTION_NOT_IMPLEMENTED",
                category=ErrorCategory.VALIDATION,
                context=ErrorContext(component_type="task", component_id=self.config.name),
            )

    @property
    def result(self) -> Any:
        """Get the result of the last task execution."""
        return self._result

    def run(self, *args, **kwargs: Any) -> Any:
        with self, self.error_context(kwargs):
            self._validate_task()
            prepared_kwargs = self._prepare_kwargs(args, kwargs)
            self._result = self.config.func(**prepared_kwargs)
            return self._result

    async def arun(self, *args, **kwargs: Any) -> Any:
        with self, self.error_context(kwargs):
            self._validate_task()
            prepared_kwargs = self._prepare_kwargs(args, kwargs)
            self._result = await self.config.func(**prepared_kwargs)
            return self._result


def task(wrapped: Callable | None = None, *, name: str | None = None, description: str | None = None, dependencies: list[str] = None) -> Callable:
    """Decorator to create a task.

    Args:
        wrapped: The function to wrap
        name: Optional name for the task
        description: Optional description of the task
        dependencies: Optional list of task names that must complete before this task

    """

    def decorator(wrapped_func):
        # Get metadata from the function
        func_metadata = get_function_metadata(wrapped_func)
        _name = name or func_metadata.name

        validate_component_name(_name, "task")

        # Create task configuration
        _task = TaskConfig(
            name=_name,
            description=description or func_metadata.description,
            slug=_name.lower().replace(" ", "_"),
            func=wrapped_func,
            input_parameters=func_metadata.input_parameters,
            output_parameters=func_metadata.output_parameters,
        )

        _task_instance = Task(_task)
        TaskConfig.register(_task_instance)

        @wrapt.decorator
        def wrapper(wrapped_func, instance, args, kwargs):
            if asyncio.iscoroutinefunction(wrapped_func):

                async def run():
                    kwargs.update(zip(wrapped_func.__code__.co_varnames, args, strict=False))
                    return await _task_instance.arun(**kwargs)

                return run()

            kwargs.update(zip(wrapped_func.__code__.co_varnames, args, strict=False))
            return _task_instance(**kwargs)

        wrapped = wrapper(wrapped_func)
        wrapped.__agentifyme = _task_instance
        wrapped.__agentifyme_metadata = {
            "type": "task",
            "name": _task.name,
            "description": _task.description,
            "input_parameters": {name: param.name for name, param in _task.input_parameters.items()},
            "output_parameters": [param.name for param in _task.output_parameters],
        }
        return wrapped

    return decorator(wrapped) if wrapped is not None else decorator
