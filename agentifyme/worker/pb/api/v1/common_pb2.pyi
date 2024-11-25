from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorkerJobStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKER_JOB_STATUS_UNSPECIFIED: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_QUEUED: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_PROCESSING: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_COMPLETED: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_FAILED: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_RETRYING: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_CANCELLED: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_TIMEOUT: _ClassVar[WorkerJobStatus]
    WORKER_JOB_STATUS_PAUSED: _ClassVar[WorkerJobStatus]
WORKER_JOB_STATUS_UNSPECIFIED: WorkerJobStatus
WORKER_JOB_STATUS_QUEUED: WorkerJobStatus
WORKER_JOB_STATUS_PROCESSING: WorkerJobStatus
WORKER_JOB_STATUS_COMPLETED: WorkerJobStatus
WORKER_JOB_STATUS_FAILED: WorkerJobStatus
WORKER_JOB_STATUS_RETRYING: WorkerJobStatus
WORKER_JOB_STATUS_CANCELLED: WorkerJobStatus
WORKER_JOB_STATUS_TIMEOUT: WorkerJobStatus
WORKER_JOB_STATUS_PAUSED: WorkerJobStatus

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
    __slots__ = ("name", "slug", "description", "input_parameters", "output_parameters", "schedule", "version", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    SLUG_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    INPUT_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    name: str
    slug: str
    description: str
    input_parameters: _struct_pb2.Struct
    output_parameters: _struct_pb2.Struct
    schedule: Schedule
    version: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., slug: _Optional[str] = ..., description: _Optional[str] = ..., input_parameters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., output_parameters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., schedule: _Optional[_Union[Schedule, _Mapping]] = ..., version: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

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

class WorkflowResult(_message.Message):
    __slots__ = ("request_id", "data", "error", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    data: _struct_pb2.Struct
    error: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, request_id: _Optional[str] = ..., data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., error: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class WorkflowJob(_message.Message):
    __slots__ = ("job_id", "status", "data", "error", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    status: WorkerJobStatus
    data: WorkflowResult
    error: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, job_id: _Optional[str] = ..., status: _Optional[_Union[WorkerJobStatus, str]] = ..., data: _Optional[_Union[WorkflowResult, _Mapping]] = ..., error: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
