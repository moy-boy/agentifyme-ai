import asyncio
import functools
import inspect
import re
import warnings
from collections.abc import Callable
from datetime import timedelta
from typing import (
    Any,
    Union,
    get_args,
    get_origin,
)

from docstring_parser import Docstring, parse
from pydantic import BaseModel, ValidationError

from agentifyme.errors import (
    AgentifyMeError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
)


class Param(BaseModel):
    """Represents a parameter.

    Attributes:
        name (str): The name of the parameter.
        description (str): The description of the parameter.
        data_type (str): The data type of the parameter.
        default_value (Any): The default value of the parameter. Defaults to None.
        required (bool): Whether the parameter is required. Defaults to True.

    """

    name: str
    description: str
    data_type: str
    default_value: Any = None
    required: bool = False
    class_name: str | None = None
    nested_fields: dict[str, "Param"] = {}


class FunctionMetadata(BaseModel):
    """Represents metadata for a function.

    Attributes:
        name (str): The name of the function.
        description (str): The description of the function.
        input_params (List[Param]): The input parameters of the function.
        output_params (List[Param]): The output parameters of the function.
        doc_string (str): The docstring of the function.

    """

    name: str
    description: str
    input_parameters: dict[str, Param]
    output_parameters: list[Param]
    doc_string: str


def deprecated(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"Function {func.__name__} is deprecated",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper


def json_datatype_from_python_type(python_type: Any) -> str:
    # Boolean type
    if python_type is bool:
        return "boolean"

    # Handle Optional types
    origin = get_origin(python_type)
    if origin is Union:
        args = get_args(python_type)
        if len(args) == 2 and type(None) in args:
            # This is an Optional type
            return json_datatype_from_python_type([arg for arg in args if arg is not type(None)][0])

    # Handle List types
    if origin in (list, list) or (isinstance(python_type, type) and issubclass(python_type, list)):
        return "array"

    # Handle Dict types
    if origin in (dict, dict) or (isinstance(python_type, type) and issubclass(python_type, dict)):
        return "object"

    # Handle primitive types and BaseModel
    if isinstance(python_type, type):
        if issubclass(python_type, str):
            return "string"
        if issubclass(python_type, (int, float)):
            return "number"
        if issubclass(python_type, bool):
            return "boolean"
        if issubclass(python_type, BaseModel):
            return "object"

    # Handle Any type
    if python_type is Any:
        return "object"

    # Default case
    return "string"


def get_pydantic_fields(
    model: type[BaseModel],
    parsed_docstring: Docstring | None = None,
    is_output: bool = False,
) -> dict[str, Param]:
    fields = {}
    for name, field in model.model_fields.items():
        field_type = field.annotation
        field_description = ""

        if parsed_docstring and not is_output:
            field_description = next(
                (p.description for p in parsed_docstring.params if p.arg_name == name),
                "",
            )

        if field_description is None:
            field_description = ""

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            nested_fields = get_pydantic_fields(field_type, parsed_docstring, is_output)
            fields[name] = Param(
                name=name,
                description=field_description,
                data_type="object",
                required=field.is_required(),
                nested_fields=nested_fields,
            )
        else:
            fields[name] = Param(
                name=name,
                description=field_description,
                data_type=json_datatype_from_python_type(field_type),
                default_value=field.default if not field.is_required() else None,
                required=field.is_required(),
            )
    return fields


def get_input_parameters(func: Callable, parsed_docstring: Docstring) -> dict[str, Param]:
    sig = inspect.signature(func)
    input_parameters = {}

    for param_name, param in sig.parameters.items():
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
        default_value = param.default if param.default != inspect.Parameter.empty else None
        required = default_value is None and param.default == inspect.Parameter.empty

        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            nested_fields = get_pydantic_fields(param_type, parsed_docstring)

            input_parameters[param_name] = Param(
                name=param_name,
                description=(
                    next(
                        ("" if p.description is None else p.description for p in parsed_docstring.params if p.arg_name == param_name),
                        "",
                    )
                    if parsed_docstring
                    else ""
                ),
                data_type="object",
                default_value=default_value,
                required=required,
                nested_fields=nested_fields,
            )
        else:
            input_parameters[param_name] = Param(
                name=param_name,
                description=(
                    next(
                        ("" if p.description is None else p.description for p in parsed_docstring.params if p.arg_name == param_name),
                        "",
                    )
                    if parsed_docstring
                    else ""
                ),
                data_type=json_datatype_from_python_type(param_type),
                default_value=default_value,
                required=required,
            )

    return input_parameters


def get_output_parameters(func: Callable, parsed_docstring: Docstring | None) -> list[Param]:
    signature = inspect.signature(func)
    return_annotation = signature.return_annotation
    return_description = parsed_docstring.returns.description if parsed_docstring and parsed_docstring.returns else ""

    if isinstance(return_annotation, type) and issubclass(return_annotation, BaseModel):
        nested_fields = get_pydantic_fields(return_annotation, parsed_docstring, is_output=True)
        return [
            Param(
                name="return_value",
                description=return_description,
                data_type="object",
                required=False,  # output is always considered optional
                nested_fields=nested_fields,
            ),
        ]
    return [
        Param(
            name="return_value",
            description=return_description,
            data_type=json_datatype_from_python_type(return_annotation),
            required=False,  # output is always considered optional
        ),
    ]


def get_function_metadata(func: Callable) -> FunctionMetadata:
    """Get metadata for a function.
    """
    # Get function name
    name = func.__name__

    # Parse docstring
    docstring = inspect.getdoc(func)
    parsed_docstring = parse(docstring) if docstring else None

    # Get description
    description: str = ""
    if parsed_docstring and parsed_docstring.short_description is not None:
        description = parsed_docstring.short_description

    # Get input and output parameters
    input_parameters = get_input_parameters(func, parsed_docstring)
    output_parameters = get_output_parameters(func, parsed_docstring)

    return FunctionMetadata(
        name=name,
        description=description,
        input_parameters=input_parameters,
        output_parameters=output_parameters,
        doc_string=docstring or "",
    )


def convert_json_to_args(func: Callable, json_data: dict[str, Any]) -> dict[str, Any]:
    """Convert JSON data to function arguments based on function signature and type hints.

    Args:
        func (callable): The function to convert arguments for.
        json_data (Dict[str, Any]): The JSON data to convert.

    Returns:
        Dict[str, Any]: A dictionary of converted arguments.

    Raises:
        ValueError: If the JSON data is invalid or doesn't match the function signature.

    """
    signature = inspect.signature(func)
    converted_args = {}

    for param_name, param in signature.parameters.items():
        if param_name not in json_data:
            if param.default is inspect.Parameter.empty:
                raise ValueError(f"Missing required parameter: {param_name}")
            continue

        param_type = param.annotation
        value = json_data[param_name]

        if isinstance(param_type, type) and issubclass(param_type, BaseModel):
            try:
                # If the value is already a Pydantic model instance, use it directly
                if isinstance(value, param_type):
                    converted_args[param_name] = value
                else:
                    # Otherwise, create a new instance
                    converted_args[param_name] = param_type(**value)
            except ValidationError as e:
                raise ValueError(f"Invalid data for parameter {param_name}: {e!s}")
        else:
            converted_args[param_name] = value

    return converted_args


@deprecated
async def validate_and_call_workflow(workflow_func: Callable, json_data: dict[str, Any]) -> Any:
    """Validate the JSON data against the workflow function's metadata and call the function.

    Args:
        workflow_func (Callable): The workflow function to be called.
        json_data (Dict[str, Any]): The JSON data to be used as arguments.

    Returns:
        Any: The result of the workflow function.

    Raises:
        ValueError: If the JSON data is invalid or doesn't match the function signature.

    """
    return await execute_function(workflow_func, json_data)


def validate_input_parameters(func: Callable, json_data: dict[str, Any]):
    # Get function metadata
    metadata: FunctionMetadata = get_function_metadata(func)
    # Validate input parameters
    for param_name, param in metadata.input_parameters.items():
        if param.required and param_name not in json_data:
            raise ValueError(f"Missing required parameter: {param_name}")

        if param_name in json_data:
            # You might want to add more specific type checking here
            if param.data_type == "object" and not (isinstance(json_data[param_name], dict) or isinstance(json_data[param_name], BaseModel)):
                raise ValueError(f"Invalid type for parameter {param_name}. Expected object, got {type(json_data[param_name])}")
            if param.data_type == "array" and not isinstance(json_data[param_name], list):
                raise ValueError(f"Invalid type for parameter {param_name}. Expected array, got {type(json_data[param_name])}")


def execute_function_sync(func: Callable, json_data: dict[str, Any]) -> Any:
    """Executes the given function with the provided JSON data as arguments.

    Args:
        func (Callable): The function to be executed.
        json_data (Dict[str, Any]): The JSON data containing the arguments for the function.

    Raises:
        ValueError: If a required parameter is missing or if the type of a parameter is invalid.

    Returns:
        Any: The result of the function execution.

    """
    # Convert JSON to function arguments
    args = convert_json_to_args(func, json_data)

    # Call the function
    result = func(**args)

    return result


async def execute_function_async(func: Callable, json_data: dict[str, Any]) -> Any:
    """Executes the given function with the provided JSON data as arguments.

    Args:
        func (Callable): The function to be executed.
        json_data (Dict[str, Any]): The JSON data containing the arguments for the function.

    Raises:
        ValueError: If a required parameter is missing or if the type of a parameter is invalid.

    Returns:
        Any: The result of the function execution.

    """
    # Convert JSON to function arguments
    args = convert_json_to_args(func, json_data)

    result = await func(**args)

    return result


def execute_function(func: Callable, json_data: dict[str, Any]) -> Any:
    """Executes the given function with the provided JSON data as arguments.

    Args:
        func (Callable): The function to be executed.
        json_data (Dict[str, Any]): The JSON data containing the arguments for the function.

    Raises:
        ValueError: If a required parameter is missing or if the type of a parameter is invalid.

    Returns:
        Any: The result of the function execution.

    """
    if asyncio.iscoroutinefunction(func):
        return asyncio.run(execute_function_async(func, json_data))
    return execute_function_sync(func, json_data)


def timedelta_to_cron(td: timedelta) -> str:
    """Convert a timedelta object to a cron expression.
    Returns a cron string in format: minute hour day month dow
    Only handles periods up to 1 month.
    """
    total_minutes = int(td.total_seconds() / 60)

    # Handle common cases
    if total_minutes == 0:
        return "* * * * *"  # Every minute
    if total_minutes == 60:
        return "0 * * * *"  # Every hour
    if total_minutes == 1440:
        return "0 0 * * *"  # Every day

    minutes = total_minutes % 60
    hours = (total_minutes // 60) % 24
    days = total_minutes // (24 * 60)

    if days > 31:
        raise ValueError("Timedelta too large - max 31 days supported")

    # Build cron components
    minute_expr = str(minutes) if minutes else "0"
    hour_expr = str(hours) if hours else "0"
    day_expr = f"*/{days}" if days else "*"

    return f"{minute_expr} {hour_expr} {day_expr} * *"


class InvalidNameError(AgentifyMeError):
    def __init__(self, name: str, component_type: str):
        super().__init__(
            message=f"{component_type} name '{name}' must be hyphen-separated or underscore-separated alphanumeric (e.g., 'my-{component_type}-123' or 'my_{component_type}_123')",
            error_code="INVALID_NAME",
            category=ErrorCategory.VALIDATION,
            context=ErrorContext(component_type=component_type, component_id="name_validation"),
            severity=ErrorSeverity.ERROR,
        )


def validate_component_name(name: str, component_type: str) -> None:
    if not re.match(r"^[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*$", name):
        raise InvalidNameError(name=name, component_type=component_type)
