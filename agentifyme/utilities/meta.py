import ast
import inspect
from datetime import date, datetime
from enum import Enum
from textwrap import dedent
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID

from docstring_parser import parse
from pydantic import BaseModel, Field


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
    class_name: Optional[str] = None


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
    input_parameters: Dict[str, Param] = Field(default_factory=dict)
    output_parameters: Dict[str, Param] = Field(default_factory=dict)
    doc_string: str


def json_datatype_from_python_type(python_type: Any) -> str:
    """
    Converts a Python data type to its corresponding JSON data type.
    """
    if python_type in (str, "<class 'str'>", date, datetime, UUID):
        return "string"
    if python_type in (int, float, "<class 'int'>", "<class 'float'>"):
        return "number"
    if python_type in (bool, "<class 'bool'>"):
        return "boolean"
    if python_type in (list, List, "<class 'list'>") or (
        hasattr(python_type, "__origin__") and python_type.__origin__ is list
    ):
        return "array"
    if python_type in (dict, Dict, "<class 'dict'>", "object") or (
        hasattr(python_type, "__origin__") and python_type.__origin__ is dict
    ):
        return "object"
    if python_type is type(None) or python_type is None:
        return "null"
    if isinstance(python_type, str):
        try:
            return json_datatype_from_python_type(eval(python_type))
        except:
            return "string"
    if inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        return "object"
    if inspect.isclass(python_type) and issubclass(python_type, Enum):
        return "string"
    if hasattr(python_type, "__origin__"):
        if python_type.__origin__ is Union:
            non_none_types = [t for t in python_type.__args__ if t is not type(None)]
            if len(non_none_types) == 1:
                return json_datatype_from_python_type(non_none_types[0])
            else:
                return "object"  # or you could return a union of types if your schema supports it
        elif python_type.__origin__ is Optional:
            return json_datatype_from_python_type(python_type.__args__[0])

    return "string"  # def


def process_return_annotation(
    return_annotation: Any, fn_return_description: str
) -> List[Param]:
    """
    Process the return annotation and generate appropriate Param objects.
    """
    output_parameters: List[Param] = []

    if return_annotation == inspect.Signature.empty or return_annotation is None:
        return output_parameters

    if get_origin(return_annotation) is Union:
        union_types = get_args(return_annotation)
        for union_type in union_types:
            if union_type is type(None):  # Handle Optional (Union with None)
                continue
            if inspect.isclass(union_type) and issubclass(union_type, BaseModel):
                # Handle BaseModel in Union
                for field_name, model_field in union_type.model_fields.items():
                    if model_field is None:
                        continue
                    _param = Param(
                        name=field_name,
                        description="",
                        data_type=json_datatype_from_python_type(
                            model_field.annotation
                        ),
                        default_value=model_field.default,
                        required=model_field.is_required(),
                    )
                    output_parameters.append(_param)
            else:
                # Handle other types in Union
                _param = Param(
                    name="output",
                    description=fn_return_description,
                    data_type=json_datatype_from_python_type(union_type),
                    default_value=(
                        []
                        if json_datatype_from_python_type(union_type) == "array"
                        else None
                    ),
                    required=True,
                )
                output_parameters.append(_param)
    elif inspect.isclass(return_annotation) and issubclass(
        return_annotation, BaseModel
    ):
        for field_name, model_field in return_annotation.model_fields.items():
            if model_field is None:
                continue
            _param = Param(
                name=field_name,
                description="",
                data_type=json_datatype_from_python_type(model_field.annotation),
                default_value=model_field.default,
                required=model_field.is_required(),
            )
            output_parameters.append(_param)
    else:
        # Handle simple return types and other complex types
        data_type = json_datatype_from_python_type(return_annotation)
        default_value = None
        if data_type == "string":
            default_value = ""
        elif data_type == "array":
            default_value = []

        _param = Param(
            name="output",
            description=fn_return_description,
            data_type=data_type,
            default_value=default_value,
            required=True,
        )
        output_parameters.append(_param)

    return output_parameters


def process_input_type(
    param_name: str, param_type: Any, default_value: Any, description: str
) -> List[Param]:
    """
    Process input type and generate appropriate Param objects.
    """
    params = []

    if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
        for field_name, model_field in param_type.model_fields.items():
            if model_field is None:
                continue
            field_type = model_field.annotation
            params.append(
                Param(
                    name=f"{param_name}.{field_name}",
                    description=model_field.description or description or "",
                    data_type=json_datatype_from_python_type(field_type),
                    default_value=model_field.default,
                    required=model_field.is_required(),
                )
            )
    elif get_origin(param_type) is Union:
        union_types = get_args(param_type)
        for union_type in union_types:
            if union_type is type(None):
                continue
            params.extend(
                process_input_type(
                    param_name, union_type, default_value, description=description or ""
                )
            )
    elif get_origin(param_type) in (list, List):
        item_type = get_args(param_type)[0]
        params.append(
            Param(
                name=param_name,
                description=description or "",
                data_type="array",
                default_value=(
                    default_value if default_value != inspect.Parameter.empty else None
                ),
                required=default_value == inspect.Parameter.empty,
            )
        )
        params.extend(
            process_input_type(
                f"{param_name}[]", item_type, None, description=description or ""
            )
        )
    else:
        params.append(
            Param(
                name=param_name,
                description=description or "",
                data_type=json_datatype_from_python_type(param_type),
                default_value=(
                    default_value if default_value != inspect.Parameter.empty else None
                ),
                required=default_value == inspect.Parameter.empty,
            )
        )

    return params


def get_function_metadata_with_ast(func: Callable) -> Tuple[List[str], List[str], str]:
    """
    Get metadata for a function.

    Args:
        func (Callable): The function to analyze.

    Returns:
        Tuple[List[str], List[str], str]: A tuple containing:
            - List of argument names
            - List of argument type annotations (or "Any" if not specified)
            - Return type annotation (or "Any" if not specified)
    """
    # Get the source code of the function
    source = inspect.getsource(func)
    source = dedent(source)

    # Parse the source code into an AST
    tree = ast.parse(source)

    # Find the function definition node
    function_def = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    )

    # Extract argument names and type annotations
    args = []
    arg_types = []
    for arg in function_def.args.args:
        args.append(arg.arg)
        if arg.annotation:
            arg_types.append(ast.unparse(arg.annotation))
        else:
            arg_types.append("Any")

    # Extract return type annotation
    if function_def.returns:
        return_type = ast.unparse(function_def.returns)
    else:
        return_type = "Any"

    return args, arg_types, return_type


def function_metadata(func: Callable) -> FunctionMetadata:
    """
    Get metadata for a function.
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

    # Get type hints
    type_hints = get_type_hints(func)

    # AST
    ast_hints = get_function_metadata_with_ast(func)

    sig = inspect.signature(func)
    func_args = get_args(sig.parameters)

    input_parameters: List[Param] = []
    for param in sig.parameters.values():
        if param.name == "self":
            continue

        param_doc = next((p for p in fn_parameters if p.arg_name == param.name), None)
        print("Param doc:", param_doc)

        print("Param:", param)
        print("Param annotation:", param.annotation)
        print("Param default:", param.default)

        if param.annotation != inspect.Parameter.empty:
            param_type = param.annotation
        elif param_doc:
            param_type = param_doc.type_name
        else:
            param_type = "string"

        param_description = param_doc.description if param_doc else ""

        input_parameters.extend(
            process_input_type(param.name, param_type, param.default, param_description)
        )

    output_parameters = process_return_annotation(
        sig.return_annotation, fn_return_description
    )

    metadata = FunctionMetadata(
        name=func.__name__,
        description=fn_short_description,
        input_params=input_parameters,
        output_params=output_parameters,
        doc_string=doc_string or "",
    )
    return metadata
