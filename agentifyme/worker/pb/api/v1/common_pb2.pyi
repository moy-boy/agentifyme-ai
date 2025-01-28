from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorkflowExecutionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKFLOW_EXECUTION_STATUS_UNSPECIFIED: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_WAITING: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_RUNNING: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_SUCCEEDED: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_FAILED: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_RETRYING: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_CANCELLED: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_TIMED_OUT: _ClassVar[WorkflowExecutionStatus]
    WORKFLOW_EXECUTION_STATUS_PAUSED: _ClassVar[WorkflowExecutionStatus]
WORKFLOW_EXECUTION_STATUS_UNSPECIFIED: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_WAITING: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_RUNNING: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_SUCCEEDED: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_FAILED: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_RETRYING: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_CANCELLED: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_TIMED_OUT: WorkflowExecutionStatus
WORKFLOW_EXECUTION_STATUS_PAUSED: WorkflowExecutionStatus

class Param(_message.Message):
    __slots__ = ("name", "description", "data_type", "default_value", "required", "class_name", "nested_fields")
    class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DATA_TYPE_UNSPECIFIED: _ClassVar[Param.DataType]
        DATA_TYPE_STRING: _ClassVar[Param.DataType]
        DATA_TYPE_INTEGER: _ClassVar[Param.DataType]
        DATA_TYPE_FLOAT: _ClassVar[Param.DataType]
        DATA_TYPE_BOOLEAN: _ClassVar[Param.DataType]
        DATA_TYPE_ARRAY: _ClassVar[Param.DataType]
        DATA_TYPE_OBJECT: _ClassVar[Param.DataType]
        DATA_TYPE_DATETIME: _ClassVar[Param.DataType]
        DATA_TYPE_DURATION: _ClassVar[Param.DataType]
    DATA_TYPE_UNSPECIFIED: Param.DataType
    DATA_TYPE_STRING: Param.DataType
    DATA_TYPE_INTEGER: Param.DataType
    DATA_TYPE_FLOAT: Param.DataType
    DATA_TYPE_BOOLEAN: Param.DataType
    DATA_TYPE_ARRAY: Param.DataType
    DATA_TYPE_OBJECT: Param.DataType
    DATA_TYPE_DATETIME: Param.DataType
    DATA_TYPE_DURATION: Param.DataType
    class NestedFieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Param
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Param, _Mapping]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    NESTED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    data_type: Param.DataType
    default_value: _any_pb2.Any
    required: bool
    class_name: str
    nested_fields: _containers.MessageMap[str, Param]
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., data_type: _Optional[_Union[Param.DataType, str]] = ..., default_value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., required: bool = ..., class_name: _Optional[str] = ..., nested_fields: _Optional[_Mapping[str, Param]] = ...) -> None: ...

class Schedule(_message.Message):
    __slots__ = ("cron_expression", "interval")
    CRON_EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_FIELD_NUMBER: _ClassVar[int]
    cron_expression: str
    interval: _duration_pb2.Duration
    def __init__(self, cron_expression: _Optional[str] = ..., interval: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class WorkflowConfig(_message.Message):
    __slots__ = ("id", "name", "slug", "description", "input_parameters", "output_parameters", "schedule", "version", "metadata")
    class InputParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Param
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Param, _Mapping]] = ...) -> None: ...
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SLUG_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    INPUT_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    slug: str
    description: str
    input_parameters: _containers.MessageMap[str, Param]
    output_parameters: _containers.RepeatedCompositeFieldContainer[Param]
    schedule: Schedule
    version: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., slug: _Optional[str] = ..., description: _Optional[str] = ..., input_parameters: _Optional[_Mapping[str, Param]] = ..., output_parameters: _Optional[_Iterable[_Union[Param, _Mapping]]] = ..., schedule: _Optional[_Union[Schedule, _Mapping]] = ..., version: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ListWorkflowsRequest(_message.Message):
    __slots__ = ("deployment_id",)
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    deployment_id: str
    def __init__(self, deployment_id: _Optional[str] = ...) -> None: ...

class ListWorkflowsResponse(_message.Message):
    __slots__ = ("workflows",)
    WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    workflows: _containers.RepeatedCompositeFieldContainer[WorkflowConfig]
    def __init__(self, workflows: _Optional[_Iterable[_Union[WorkflowConfig, _Mapping]]] = ...) -> None: ...

class InboundClientMessage(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OutboundClientMessage(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AgentifyMeError(_message.Message):
    __slots__ = ("message", "error_code", "category", "severity", "traceback", "error_type")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    TRACEBACK_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    message: str
    error_code: str
    category: str
    severity: str
    traceback: str
    error_type: str
    def __init__(self, message: _Optional[str] = ..., error_code: _Optional[str] = ..., category: _Optional[str] = ..., severity: _Optional[str] = ..., traceback: _Optional[str] = ..., error_type: _Optional[str] = ...) -> None: ...

class WorkflowExecutionResult(_message.Message):
    __slots__ = ("data", "error", "status")
    DATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    data: _struct_pb2.Value
    error: AgentifyMeError
    status: WorkflowExecutionStatus
    def __init__(self, data: _Optional[_Union[_struct_pb2.Value, _Mapping]] = ..., error: _Optional[_Union[AgentifyMeError, _Mapping]] = ..., status: _Optional[_Union[WorkflowExecutionStatus, str]] = ...) -> None: ...

class WorkflowExecutionError(_message.Message):
    __slots__ = ("message", "error_code", "category", "severity", "traceback", "error_type")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    TRACEBACK_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    message: str
    error_code: str
    category: str
    severity: str
    traceback: str
    error_type: str
    def __init__(self, message: _Optional[str] = ..., error_code: _Optional[str] = ..., category: _Optional[str] = ..., severity: _Optional[str] = ..., traceback: _Optional[str] = ..., error_type: _Optional[str] = ...) -> None: ...

class MessageAck(_message.Message):
    __slots__ = ("msg_id", "success", "error")
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    msg_id: str
    success: bool
    error: str
    def __init__(self, msg_id: _Optional[str] = ..., success: bool = ..., error: _Optional[str] = ...) -> None: ...

class LivenessCheckRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class LivenessCheckResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ReadinessCheckRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ReadinessCheckResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...
