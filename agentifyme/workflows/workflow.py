from typing import Any, Callable, List, Optional, ParamSpec, TypeVar, Union, overload

from agentifyme.base_config import BaseConfig, BaseModule
from agentifyme.utilities.log import getLogger
from agentifyme.utilities.meta import Param, function_metadata

P = ParamSpec("P")
R = TypeVar("R", bound=Callable[..., Any])

logger = getLogger()


class WorkflowError(Exception):
    pass


class WorfklowExecutionError(WorkflowError):
    pass


class WorkflowConfig(BaseConfig):
    """
    Represents a workflow in the system.

    Attributes:
        name (str): The name of the workflow.
        slug (str): The slug of the workflow.
        description (Optional[str]): The description of the workflow (optional).
        func (Callable[..., Any]): The function associated with the workflow.
        input_params (List[Param]): The list of input parameters for the workflow.
        output_params (List[Param]): The list of output parameters for the workflow.
    """

    input_params: List[Param]
    output_params: List[Param]


class Workflow(BaseModule):
    def __init__(self, config: WorkflowConfig, *args, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.config = config

    def run(self, *args: Any, **kwargs: Any) -> Any:
        print("Workflow.run", args, kwargs)
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            return self.config.func(**kwargs)


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
) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func_metadata = function_metadata(func)

        _name = name or func_metadata.name
        _workflow = WorkflowConfig(
            name=_name,
            description=description or func_metadata.description,
            slug=_name.lower().replace(" ", "_"),
            func=func,
            input_params=func_metadata.input_params,
            output_params=func_metadata.output_params,
        )
        _workflow_instance = Workflow(_workflow)
        WorkflowConfig.register(_workflow_instance)

        def wrapper(*args, **kwargs) -> Any:
            result = _workflow_instance(*args, **kwargs)
            return result

        return wrapper

    if callable(func):
        return decorator(func)
    elif name is not None:

        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            return decorator(func)

        return decorator
    else:
        raise WorkflowError("Invalid arguments for workflow decorator")
