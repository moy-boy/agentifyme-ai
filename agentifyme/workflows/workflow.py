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

from agentifyme.base_config import BaseConfig, BaseModule
from agentifyme.logger import get_logger
from agentifyme.utilities.func_utils import (
    Param,
    execute_function,
    get_function_metadata,
)

P = ParamSpec("P")
R = TypeVar("R", bound=Callable[..., Any])

logger = get_logger()


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

    input_parameters: Dict[str, Param]
    output_parameters: List[Param]


class Workflow(BaseModule):
    def __init__(self, config: WorkflowConfig, *args, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.config = config

    def run(self, *args, **kwargs: Any) -> Any:
        logger.info(f"Running workflow: {self.config.name}")
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            result = execute_function(self.config.func, kwargs)
            return result
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
) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func_metadata = get_function_metadata(func)
        _name = name or func_metadata.name
        _workflow = WorkflowConfig(
            name=_name,
            description=description or func_metadata.description,
            slug=_name.lower().replace(" ", "_"),
            func=func,
            input_parameters=func_metadata.input_parameters,
            output_parameters=func_metadata.output_parameters,
        )
        _workflow_instance = Workflow(_workflow)
        WorkflowConfig.register(_workflow_instance)

        def wrapper(*args, **kwargs) -> Any:
            kwargs.update(zip(func.__code__.co_varnames, args))
            result = _workflow_instance(**kwargs)
            return result

        # pylint: disable=protected-access
        wrapper.__agentifyme = _workflow_instance  # type: ignore

        return wrapper

    if callable(func):
        return decorator(func)
    elif name is not None:
        return decorator
    else:
        raise WorkflowError("Invalid arguments for workflow decorator")
