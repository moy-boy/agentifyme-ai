import inspect
import re
from typing import Any, Callable, Dict, List, get_origin

from docstring_parser import parse
from pydantic import BaseModel

from agentifyme.cache import F


class Param(BaseModel):
    """
    Represents a parameter.

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

    class Config:
        """Pydantic configuration."""

        frozen = True


class FunctionMetadata(BaseModel):
    """
    Represents metadata for a function.

    Attributes:
        name (str): The name of the function.
        description (str): The description of the function.
        input_params (List[Param]): The input parameters of the function.
        output_params (List[Param]): The output parameters of the function.
        doc_string (str): The docstring of the function.
    """

    name: str
    description: str
    input_params: List[Param]
    output_params: List[Param]
    doc_string: str

    class Config:
        """Pydantic configuration."""

        frozen = True


def json_datatype_from_python_type(python_type: str | None) -> str:
    """
    Converts a Python data type to its corresponding JSON data type.

    Args:
        python_type (str | None): The Python data type to be converted.

    Returns:
        str: The corresponding JSON data type.

    Raises:
        None

    Examples:
        >>> json_datatype_from_python_type("str")
        "string"
        >>> json_datatype_from_python_type("int")
        "number"
        >>> json_datatype_from_python_type("float")
        "number"
        >>> json_datatype_from_python_type("bool")
        "boolean"
        >>> json_datatype_from_python_type("list")
        "array"
        >>> json_datatype_from_python_type(None)
        "string"
    """
    if python_type == "str":
        return "string"
    if python_type == "int":
        return "number"
    if python_type == "float":
        return "number"
    if python_type == "bool":
        return "boolean"
    if python_type == "list":
        return "array"
    return "string"


def function_metadata(func: Callable) -> FunctionMetadata:
    """
    Get metadata for a function.

    Args:
        func (Callable): The function to get metadata for.

    Returns:
        FunctionMetadata: The metadata for the function.
    """
    fn_short_description = ""
    fn_parameters = []
    fn_return_description = ""

    doc_string = inspect.getdoc(func)
    if doc_string:
        parsed_docstring = parse(doc_string)

        if parsed_docstring.returns and parsed_docstring.returns.description:
            fn_return_description = parsed_docstring.returns.description

        if parsed_docstring.short_description:
            fn_short_description = parsed_docstring.short_description

        fn_parameters = parsed_docstring.params

    sig = inspect.signature(func)
    input_parameters: List[Param] = []
    for param in sig.parameters.values():
        # ignore self parameter
        if param.name == "self":
            continue

        param_doc = next((p for p in fn_parameters if p.arg_name == param.name), None)

        param_type = (
            str(param_doc.type_name)
            if param_doc and param.annotation != inspect.Parameter.empty
            else "string"
        )

        # Determine if parameter is optional based on its default value
        is_optional = param.default != inspect.Parameter.empty
        param_desc = (
            param_doc.description if param_doc and param_doc.description else ""
        )

        _param = Param(
            name=param.name,
            description=param_desc,
            data_type=json_datatype_from_python_type(param_type),
            default_value=(
                param.default if param.default != inspect.Parameter.empty else None
            ),
            required=not is_optional,
        )

        input_parameters.append(_param)

    output_parameters: List[Param] = []
    return_annotation = sig.return_annotation

    if return_annotation != inspect.Signature.empty:
        if inspect.isclass(return_annotation):
            if issubclass(return_annotation, str):
                _param = Param(
                    name="output",
                    description=fn_return_description,
                    data_type="string",
                    default_value="",
                    required=True,
                )
                output_parameters.append(_param)

            elif issubclass(return_annotation, BaseModel):
                for field_name, model_field in return_annotation.model_fields.items():
                    if model_field is None:
                        continue

                    _param = Param(
                        name=field_name,
                        description="",
                        data_type=json_datatype_from_python_type(
                            str(model_field.annotation)
                        ),
                        default_value=model_field.default,
                        required=model_field.is_required(),
                    )
                    output_parameters.append(_param)

        if get_origin(return_annotation) is not None:
            if issubclass(get_origin(return_annotation), list):
                _param = Param(
                    name="output",
                    description=fn_return_description,
                    data_type="array",
                    default_value=[],
                    required=True,
                )
                output_parameters.append(_param)

    metadata = FunctionMetadata(
        name=func.__name__,
        description=fn_short_description,
        input_params=input_parameters,
        output_params=output_parameters,
        doc_string=doc_string or "",
    )
    return metadata
