import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import wrapt

from agentifyme.components.base import BaseConfig, RunnableComponent
from agentifyme.errors import AgentifyMeValidationError, ErrorCategory, ErrorContext

from .utils import (
    Param,
    get_function_metadata,
    timedelta_to_cron,
    validate_component_name,
)


@dataclass
class WorkflowConfig(BaseConfig):
    """Represents a workflow.

    Attributes:
        name (str): The name of the workflow.
        slug (str): The slug of the workflow.
        description (Optional[str]): The description of the workflow (optional).
        func (Callable[..., Any]): The function associated with the workflow.
        input_parameters (dict[str, Param]): A dictionary of input parameters for the workflow.
        output_parameters (list[Param]): The list of output parameters for the workflow.
        schedule (Optional[Union[str, timedelta]]): The schedule for the workflow.
            Can be either a cron expression string or a timedelta object.

    """

    input_parameters: dict[str, Param] = field(default_factory=dict)
    output_parameters: list[Param] = field(default_factory=list)
    schedule: str | timedelta | None = None

    @classmethod
    def normalize_schedule(cls, v: str | timedelta | None) -> str | None:
        if isinstance(v, timedelta):
            try:
                return timedelta_to_cron(v)
            except ValueError as e:
                raise ValueError(f"Cannot convert this timedelta to a cron expression: {e}")
        return v  # Return as-is if it's already a string or None


class Workflow(RunnableComponent):
    component_type: str = "workflow"
    config: WorkflowConfig

    def __init__(self, config: WorkflowConfig, **kwargs) -> None:
        super().__init__(component_type=self.component_type, config=config)
        self.config = config
        self.run_id = kwargs.get("run_id")

    def _validate_workflow(self) -> None:
        """Validate that the workflow function is implemented."""
        if not self.config.func:
            raise AgentifyMeValidationError(
                message="Workflow function not implemented",
                error_code="WORKFLOW_FUNCTION_NOT_IMPLEMENTED",
                category=ErrorCategory.VALIDATION,
                context=ErrorContext(component_type="workflow", component_id=self.config.name),
            )

    def run(self, *args, **kwargs: Any) -> Any:
        with self, self.error_context(kwargs):
            self._validate_workflow()
            self.current_kwargs = self._prepare_kwargs(args, kwargs)
            return self.config.func(**self.current_kwargs)

    async def arun(self, *args, **kwargs: Any) -> Any:
        with self, self.error_context(kwargs):
            self._validate_workflow()
            self.current_kwargs = self._prepare_kwargs(args, kwargs)
            return await self.config.func(**self.current_kwargs)


def workflow(wrapped: Callable | None = None, *, name: str | None = None, description: str | None = None, schedule: str | timedelta | None = None) -> Callable:
    def decorator(wrapped_func):
        func_metadata = get_function_metadata(wrapped_func)
        _name = name or func_metadata.name
        validate_component_name(_name, "workflow")

        _workflow = WorkflowConfig(
            name=_name,
            description=description or func_metadata.description,
            slug=_name.lower().replace(" ", "_"),
            func=wrapped_func,
            input_parameters=func_metadata.input_parameters,
            output_parameters=func_metadata.output_parameters,
            schedule=schedule,
        )
        _workflow_instance = Workflow(_workflow)
        WorkflowConfig.register(_workflow_instance)

        @wrapt.decorator
        def wrapper(wrapped_func, instance, args, kwargs):
            if asyncio.iscoroutinefunction(wrapped_func):

                async def run():
                    kwargs.update(zip(wrapped_func.__code__.co_varnames, args, strict=False))
                    return await _workflow_instance.arun(**kwargs)

                return run()

            kwargs.update(zip(wrapped_func.__code__.co_varnames, args, strict=False))
            return _workflow_instance(**kwargs)

        wrapped = wrapper(wrapped_func)
        wrapped.__agentifyme = _workflow_instance
        wrapped.__agentifyme_metadata = {
            "type": "workflow",
            "name": _workflow.name,
            "description": _workflow.description,
            "input_parameters": {name: param.name for name, param in _workflow.input_parameters.items()},
            "output_parameters": [param.name for param in _workflow.output_parameters],
            "schedule": _workflow.schedule,
        }
        return wrapped

    return decorator(wrapped) if wrapped is not None else decorator
