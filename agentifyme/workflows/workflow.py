from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    Union,
    overload,
)

from pydantic import BaseModel, Field, create_model

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

    input_params: List[Param] = Field(default_factory=list)
    output_params: List[Param] = Field(default_factory=list)


class Workflow(BaseModule):
    def __init__(self, config: WorkflowConfig, *args, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.config = config
        self.input_model = self._create_input_model()
        self.output_model = self._create_output_model()

    def _create_input_model(self) -> Type[BaseModel]:
        fields = {}
        for param in self.config.input_params:
            field_type = self._get_field_type(param.data_type)
            fields[param.name] = (field_type, ... if param.required else None)
        return create_model(f"{self.config.name}Input", **fields)

    def _create_output_model(self) -> Type[BaseModel]:
        fields = {}
        for param in self.config.output_params:
            field_type = self._get_field_type(param.data_type)
            fields[param.name] = (field_type, ... if param.required else None)
        return create_model(f"{self.config.name}Output", **fields)

    def _get_field_type(self, data_type: str) -> Any:
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": List,
            "object": Dict,
        }
        return type_mapping.get(data_type, Any)

    def _parse_input(self, input_data: Dict[str, Any]) -> Any:
        parsed_input = self.input_model(**input_data)
        return parsed_input

    def _parse_output(self, output_data: Any) -> Dict[str, Any]:
        if isinstance(output_data, BaseModel):
            return output_data.model_dump()
        elif isinstance(output_data, dict):
            return self.output_model(**output_data).model_dump()
        else:
            return {self.config.output_params[0].name: output_data}

    def run(self, **kwargs: Any) -> Any:
        logger.info(f"Running workflow: {self.config.name}")
        parsed_input = self._parse_input(kwargs)
        if self.config.func:
            result = self.config.func(**parsed_input.model_dump())
            return self._parse_output(result)
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

        def wrapper(**kwargs) -> Any:
            result = _workflow_instance.run(**kwargs)
            return result

        return wrapper

    if callable(func):
        return decorator(func)
    elif name is not None:
        return decorator
    else:
        raise WorkflowError("Invalid arguments for workflow decorator")
