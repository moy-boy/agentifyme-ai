from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class JobType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    JOB_TYPE_UNSPECIFIED: _ClassVar[JobType]
    JOB_TYPE_INTERACTIVE: _ClassVar[JobType]
    JOB_TYPE_BATCH: _ClassVar[JobType]

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
JOB_TYPE_UNSPECIFIED: JobType
JOB_TYPE_INTERACTIVE: JobType
JOB_TYPE_BATCH: JobType
WORKER_JOB_STATUS_UNSPECIFIED: WorkerJobStatus
WORKER_JOB_STATUS_QUEUED: WorkerJobStatus
WORKER_JOB_STATUS_PROCESSING: WorkerJobStatus
WORKER_JOB_STATUS_COMPLETED: WorkerJobStatus
WORKER_JOB_STATUS_FAILED: WorkerJobStatus
WORKER_JOB_STATUS_RETRYING: WorkerJobStatus
WORKER_JOB_STATUS_CANCELLED: WorkerJobStatus
WORKER_JOB_STATUS_TIMEOUT: WorkerJobStatus
WORKER_JOB_STATUS_PAUSED: WorkerJobStatus

class JobStatus(_message.Message):
    __slots__ = ("job_id", "status", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    status: WorkerJobStatus
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, job_id: _Optional[str] = ..., status: _Optional[_Union[WorkerJobStatus, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class JobResult(_message.Message):
    __slots__ = ("job_id", "output", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    output: _struct_pb2.Struct
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, job_id: _Optional[str] = ..., output: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class JobError(_message.Message):
    __slots__ = ("job_id", "message", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    message: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, job_id: _Optional[str] = ..., message: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class WorkflowFunction(_message.Message):
    __slots__ = ("name", "parameters")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    name: str
    parameters: _struct_pb2.Struct
    def __init__(self, name: _Optional[str] = ..., parameters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
