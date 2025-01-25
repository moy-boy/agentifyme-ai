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
