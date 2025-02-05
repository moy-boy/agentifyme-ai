from datetime import datetime
from decimal import Decimal, InvalidOperation
from inspect import signature
from numbers import Number
from typing import Any, Callable, Union, get_args, get_origin, get_type_hints

from google.protobuf import any_pb2, struct_pb2
from google.protobuf.json_format import MessageToDict, ParseDict

from agentifyme.components.utils import Param
from agentifyme.components.workflow import WorkflowConfig
from agentifyme.worker.pb.api.v1 import common_pb2 as common_pb
from agentifyme.worker.pb.api.v1.common_pb2 import Param as ParamPb


def get_param_type_enum(data_type: str) -> ParamPb.DataType:
    """Convert string data type to protobuf Param.DataType enum.

    Args:
        data_type: String representation of the parameter type

    Returns:
        Corresponding protobuf DataType enum value, defaults to DATA_TYPE_STRING if unknown

    """
    type_mapping = {
        "string": ParamPb.DataType.DATA_TYPE_STRING,
        "str": ParamPb.DataType.DATA_TYPE_STRING,
        "integer": ParamPb.DataType.DATA_TYPE_INTEGER,
        "int": ParamPb.DataType.DATA_TYPE_INTEGER,
        "float": ParamPb.DataType.DATA_TYPE_FLOAT,
        "boolean": ParamPb.DataType.DATA_TYPE_BOOLEAN,
        "bool": ParamPb.DataType.DATA_TYPE_BOOLEAN,
        "array": ParamPb.DataType.DATA_TYPE_ARRAY,
        "list": ParamPb.DataType.DATA_TYPE_ARRAY,
        "object": ParamPb.DataType.DATA_TYPE_OBJECT,
        "dict": ParamPb.DataType.DATA_TYPE_OBJECT,
    }
    data_type_lower = data_type.lower()
    return type_mapping.get(data_type_lower, ParamPb.DataType.DATA_TYPE_STRING)


def convert_param_to_pb(param: Param) -> common_pb.Param:
    """Convert a Python Param object to protobuf Param message.

    Args:
        param: Python Param object to convert

    Returns:
        Corresponding protobuf Param message

    """
    data_type_map = {
        "string": common_pb.Param.DATA_TYPE_STRING,
        "integer": common_pb.Param.DATA_TYPE_INTEGER,
        "float": common_pb.Param.DATA_TYPE_FLOAT,
        "boolean": common_pb.Param.DATA_TYPE_BOOLEAN,
        "array": common_pb.Param.DATA_TYPE_ARRAY,
        "object": common_pb.Param.DATA_TYPE_OBJECT,
        "datetime": common_pb.Param.DATA_TYPE_DATETIME,
        "duration": common_pb.Param.DATA_TYPE_DURATION,
    }

    pb_param = common_pb.Param(
        name=param.name,
        description=param.description,
        data_type=data_type_map.get(param.data_type.lower(), common_pb.Param.DATA_TYPE_UNSPECIFIED),
        required=param.required,
        class_name=param.class_name or "",
    )

    if param.default_value is not None:
        any_value = any_pb2.Any()
        if param.data_type.lower() == "array":
            list_value = struct_pb2.ListValue()
            for item in param.default_value:
                list_value.values.append(struct_pb2.Value(string_value=str(item)))
            value = struct_pb2.Value(list_value=list_value)
        else:
            value = struct_pb2.Value(string_value=str(param.default_value))
        any_value.Pack(value)
        pb_param.default_value.CopyFrom(any_value)

    for field_name, nested_param in param.nested_fields.items():
        pb_param.nested_fields[field_name].CopyFrom(convert_param_to_pb(nested_param))

    return pb_param


def convert_workflow_to_pb(workflow: WorkflowConfig) -> common_pb.WorkflowConfig:
    """Convert a Python WorkflowConfig object to protobuf WorkflowConfig message."""
    pb_workflow = common_pb.WorkflowConfig()

    # Set basic fields
    pb_workflow.name = workflow.name
    pb_workflow.slug = workflow.slug
    pb_workflow.description = workflow.description or ""
    pb_workflow.version = getattr(workflow, "version", "")

    # Convert input parameters
    for name, param in workflow.input_parameters.items():
        pb_workflow.input_parameters[name].CopyFrom(convert_param_to_pb(param))

    # Convert output parameters
    for param in workflow.output_parameters:
        pb_param = pb_workflow.output_parameters.add()
        pb_param.CopyFrom(convert_param_to_pb(param))

    # Set schedule if it exists
    if hasattr(workflow, "schedule") and workflow.schedule is not None:
        if isinstance(workflow.schedule, str):
            pb_workflow.schedule.cron = workflow.schedule
        else:
            pb_workflow.schedule.cron = workflow.normalize_schedule(workflow.schedule)

    # Set metadata if exists
    metadata_dict = getattr(workflow, "metadata", {})
    if metadata_dict:
        pb_workflow.metadata.update(metadata_dict)

    return pb_workflow


def struct_to_dict(struct_data: struct_pb2.Struct) -> dict:
    """Convert protobuf Struct to Python dictionary."""
    if not struct_data:
        return {}
    return MessageToDict(struct_data)


def dict_to_struct(data: dict) -> struct_pb2.Struct:
    """Convert Python dictionary to protobuf Struct."""
    struct_data = struct_pb2.Struct()
    if data:
        ParseDict(data, struct_data)
    return struct_data


def _convert_numeric(value: Any, target_type: type) -> Number:
    """Convert a value to a numeric type with validation."""
    if isinstance(value, str):
        value = value.strip()
        try:
            if issubclass(target_type, int):
                float_val = float(value)
                if float_val.is_integer():
                    return int(float_val)
                raise ValueError(f"Float value {value} cannot be converted to integer without loss")
            if issubclass(target_type, float):
                return float(value)
            if issubclass(target_type, Decimal):
                return Decimal(value)
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Cannot convert {value} to {target_type.__name__}: {str(e)}")

    if isinstance(value, Number):
        if issubclass(target_type, int) and isinstance(value, float):
            if value.is_integer():
                return int(value)
            raise ValueError(f"Float value {value} cannot be converted to integer without loss")
        return target_type(value)

    raise ValueError(f"Cannot convert {type(value).__name__} to {target_type.__name__}")


def _convert_dict_values(value: dict, type_hints: Any) -> dict:
    """Convert dictionary values based on type hints."""
    if not isinstance(value, dict):
        raise ValueError(f"Expected dict but got {type(value).__name__}")

    dict_types = get_args(type_hints)
    if not dict_types:
        return value

    key_type, value_type = dict_types
    result = {}

    for k, v in value.items():
        if key_type is not Any and not isinstance(k, key_type):
            k = key_type(k)

        if value_type is Any:
            v = v
        elif get_origin(value_type) is dict:
            v = _convert_dict_values(v, value_type)
        elif get_origin(value_type) is Union:
            v = _convert_union_type(v, get_args(value_type))
        elif value_type in (int, float, Decimal):
            v = _convert_numeric(v, value_type)
        elif value_type is not Any and not isinstance(v, value_type):
            v = value_type(v)

        result[k] = v

    return result


def _convert_union_type(value: Any, union_types: tuple) -> Any:
    """Convert a value to one of the possible union types."""
    errors = []
    for possible_type in union_types:
        if possible_type is type(None):
            continue
        try:
            if possible_type in (int, float, Decimal):
                return _convert_numeric(value, possible_type)
            return possible_type(value)
        except (ValueError, TypeError) as e:
            errors.append(str(e))
    raise ValueError(f"Could not convert value to any of {union_types}: {'; '.join(errors)}")


def _convert_value(value: Any, param_type: type, param_name: str) -> Any:
    """Convert a single value to the target type."""
    try:
        # Handle dict type - check before any conversion
        if param_type is dict or get_origin(param_type) is dict:
            if not isinstance(value, dict):
                raise ValueError(f"Expected dict but got {type(value).__name__}")
            if get_origin(param_type) is dict:
                return _convert_dict_values(value, param_type)
            return value

        if hasattr(param_type, "model_validate"):
            return param_type.model_validate(value)
        if param_type == datetime:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        if param_type in (int, float, Decimal):
            return _convert_numeric(value, param_type)
        if get_origin(param_type) is Union:
            return _convert_union_type(value, get_args(param_type))
        return param_type(value)
    except ValueError as e:
        raise ValueError(str(e))


def build_args_from_signature(func: Callable, input_dict: dict[str, Any]) -> dict[str, Any]:
    """Builds function arguments using signature and type hints."""
    sig = signature(func)
    type_hints = get_type_hints(func)
    type_hints.pop("return", None)
    args = {}

    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name)
        if not param_type or (param_name not in input_dict and param.default is not param.empty):
            continue

        value = input_dict.get(param_name)
        if value is None:
            if get_origin(param_type) is Union and type(None) in get_args(param_type) or param.default is not param.empty:
                args[param_name] = None
                continue
            raise ValueError(f"Required parameter {param_name} cannot be None")

        try:
            args[param_name] = _convert_value(value, param_type, param_name)
        except ValueError as e:
            # Use the original error message directly
            raise ValueError(str(e))

    return args
