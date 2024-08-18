import ast
import asyncio
import inspect
from datetime import timedelta
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    overload,
)

from pydantic import field_validator

from agentifyme.base_config import BaseConfig, BaseModule
from agentifyme.logger import get_logger
from agentifyme.tasks import TaskConfig
from agentifyme.utilities.func_utils import (
    Param,
    execute_function,
    get_function_metadata,
)
from agentifyme.utilities.time import timedelta_to_cron

P = ParamSpec("P")
R = TypeVar("R", bound=Callable[..., Any])

logger = get_logger()


class WorkflowError(Exception):
    pass


class WorkflowExecutionError(WorkflowError):
    pass


class AsyncWorkflowExecutionError(WorkflowError):
    pass


class WorkflowConfig(BaseConfig):
    """
    Represents a workflow.

    Attributes:
        name (str): The name of the workflow.
        slug (str): The slug of the workflow.
        description (Optional[str]): The description of the workflow (optional).
        func (Callable[..., Any]): The function associated with the workflow.
        input_parameters (Dict[str, Param]): A dictionary of input parameters for the workflow.
        output_parameters (List[Param]): The list of output parameters for the workflow.
        schedule (Optional[Union[str, timedelta]]): The schedule for the workflow.
            Can be either a cron expression string or a timedelta object.
    """

    input_parameters: Dict[str, Param]
    output_parameters: List[Param]
    schedule: Optional[Union[str, timedelta]]

    @field_validator("schedule")
    @classmethod
    def normalize_schedule(cls, v: Optional[Union[str, timedelta]]) -> Optional[str]:
        if isinstance(v, timedelta):
            try:
                return timedelta_to_cron(v)
            except ValueError as e:
                raise ValueError(
                    f"Cannot convert this timedelta to a cron expression: {e}"
                )
        return v  # Return as-is if it's already a string or None


class Workflow(BaseModule):
    def __init__(self, config: WorkflowConfig, *args, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.config = config

    def run(self, *args, **kwargs: Any) -> Any:
        logger.info(f"Running workflow: {self.config.name}")
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            try:
                return execute_function(self.config.func, kwargs)
            except Exception as e:
                raise WorkflowExecutionError(
                    f"Error executing workflow {self.config.name}: {str(e)}"
                ) from e
        else:
            raise NotImplementedError("Workflow function not implemented")

    async def arun(self, *args, **kwargs: Any) -> Any:
        logger.info(f"Running async workflow: {self.config.name}")
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            try:
                if asyncio.iscoroutinefunction(self.config.func):
                    return await self.config.func(**kwargs)
                else:
                    return await asyncio.to_thread(self.config.func, **kwargs)
            except Exception as e:
                raise AsyncWorkflowExecutionError(
                    f"Error executing async workflow {self.config.name}: {str(e)}"
                ) from e
        else:
            raise NotImplementedError("Workflow function not implemented")


@overload
def workflow(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator function for defining a workflow."""


@overload
def workflow(*, name: str, description: Optional[str] = None) -> Callable[..., Any]: ...


# Implement the function
def workflow(
    func: Union[Callable[..., Any], None] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    schedule: Optional[Union[str, timedelta]] = None,
) -> Callable[..., Any]:
    def decorator(
        func: Callable[..., Any], outer_name: Optional[str] = name
    ) -> Callable[..., Any]:
        func_metadata = get_function_metadata(func)
        _name = func_metadata.name
        if outer_name:
            _name = outer_name
        _workflow = WorkflowConfig(
            name=_name,
            description=description or func_metadata.description,
            slug=_name.lower().replace(" ", "_"),
            func=func,
            input_parameters=func_metadata.input_parameters,
            output_parameters=func_metadata.output_parameters,
            schedule=schedule,
        )
        _workflow_instance = Workflow(_workflow)
        WorkflowConfig.register(_workflow_instance)

        def wrapper(*args, **kwargs) -> Any:
            kwargs.update(zip(func.__code__.co_varnames, args))
            result = _workflow_instance(**kwargs)
            return result

        async def async_wrapper(*args, **kwargs) -> Any:
            kwargs.update(zip(func.__code__.co_varnames, args))
            result = await _workflow_instance.arun(**kwargs)
            return result

        # nested_calls = []
        # source = inspect.getsource(func)
        # tree = ast.parse(source)
        # for node in ast.walk(tree):
        #     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        #         call_name = node.func.id
        #         if WorkflowConfig.get(call_name) or TaskConfig.get(call_name):
        #             nested_calls.append(call_name)

        # Choose the appropriate wrapper based on whether the function is async or not
        final_wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

        final_wrapper.__agentifyme = _workflow_instance  # type: ignore
        final_wrapper.__agentifyme_metadata = {  # type: ignore
            "type": "workflow",
            "name": _workflow.name,
            "description": _workflow.description,
            "input_parameters": {
                name: param.name for name, param in _workflow.input_parameters.items()
            },
            "output_parameters": [param.name for param in _workflow.output_parameters],
            "nested_calls": [],
            "is_async": asyncio.iscoroutinefunction(func),
        }

        return final_wrapper

    if callable(func):
        return decorator(func)
    elif name is not None:
        return decorator
    else:
        raise WorkflowError("Invalid arguments for workflow decorator")
