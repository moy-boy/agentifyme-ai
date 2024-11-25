from datetime import timedelta
from typing import Optional

from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict, ParseDict

from agentifyme.config import Param, WorkflowConfig
from agentifyme.worker.pb.api.v1 import common_pb2 as common_pb
from agentifyme.worker.pb.api.v1.common_pb2 import Param as ParamPb


def get_param_type_enum(data_type: str) -> ParamPb.DataType:
    """
    Convert string data type to protobuf Param.DataType enum.

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


def convert_param_to_pb(param: Param) -> ParamPb:
    """
    Convert a Python Param object to protobuf Param message.

    Args:
        param: Python Param object to convert

    Returns:
        Corresponding protobuf Param message
    """
    param_type = get_param_type_enum(param.data_type)

    return ParamPb(
        name=param.name,
        description=param.description,
        data_type=param_type,
        default_value=str(param.default_value)
        if param.default_value is not None
        else "",
        required=param.required,
        class_name=param.class_name or "",
        nested_fields={
            k: convert_param_to_pb(v) for k, v in param.nested_fields.items()
        },
    )


def convert_workflow_to_pb(workflow: WorkflowConfig) -> common_pb.WorkflowConfig:
    """
    Convert a Python WorkflowConfig object to protobuf WorkflowConfig message.

    Args:
        workflow: Python WorkflowConfig object to convert

    Returns:
        Corresponding protobuf WorkflowConfig message
    """
    # Convert input parameters
    pb_input_parameters = {
        key: convert_param_to_pb(param)
        for key, param in workflow.input_parameters.items()
    }

    # Convert output parameters
    pb_output_parameters = [
        convert_param_to_pb(param) for param in workflow.output_parameters
    ]

    # Convert schedule if it exists
    schedule: Optional[common_pb.Schedule] = None
    if workflow.schedule:
        if isinstance(workflow.schedule, str):
            schedule = common_pb.Schedule(cron=workflow.schedule)
        elif isinstance(workflow.schedule, timedelta):
            cron_expression = workflow.normalize_schedule(workflow.schedule)
            if cron_expression:
                schedule = common_pb.Schedule(cron=cron_expression)

    # Create the protobuf WorkflowConfig
    pb_workflow = common_pb.WorkflowConfig(
        name=workflow.name,
        slug=workflow.slug,
        description=workflow.description or "",
        input_parameters=pb_input_parameters,
        output_parameters=pb_output_parameters,
        version=getattr(workflow, "version", ""),
        metadata=getattr(workflow, "metadata", {}),
    )

    # Set schedule if it exists
    if schedule:
        pb_workflow.schedule.CopyFrom(schedule)

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
