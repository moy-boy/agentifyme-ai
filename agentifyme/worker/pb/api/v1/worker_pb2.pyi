from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

from agentifyme.worker.pb.api.v1 import common_pb2 as _common_pb2

DESCRIPTOR: _descriptor.FileDescriptor

class CommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMMAND_TYPE_UNSPECIFIED: _ClassVar[CommandType]
    COMMAND_TYPE_ABORT: _ClassVar[CommandType]
    COMMAND_TYPE_RESTART: _ClassVar[CommandType]
    COMMAND_TYPE_PAUSE: _ClassVar[CommandType]
    COMMAND_TYPE_RESUME: _ClassVar[CommandType]
    COMMAND_TYPE_CANCEL: _ClassVar[CommandType]

class WorkerStreamOutboundType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKER_SERVICE_OUTBOUND_TYPE_UNSPECIFIED: _ClassVar[WorkerStreamOutboundType]
    WORKER_SERVICE_OUTBOUND_TYPE_REGISTER: _ClassVar[WorkerStreamOutboundType]
    WORKER_SERVICE_OUTBOUND_TYPE_JOB_STATUS: _ClassVar[WorkerStreamOutboundType]
    WORKER_SERVICE_OUTBOUND_TYPE_JOB_RESULT: _ClassVar[WorkerStreamOutboundType]
    WORKER_SERVICE_OUTBOUND_TYPE_JOB_ERROR: _ClassVar[WorkerStreamOutboundType]

COMMAND_TYPE_UNSPECIFIED: CommandType
COMMAND_TYPE_ABORT: CommandType
COMMAND_TYPE_RESTART: CommandType
COMMAND_TYPE_PAUSE: CommandType
COMMAND_TYPE_RESUME: CommandType
COMMAND_TYPE_CANCEL: CommandType
WORKER_SERVICE_OUTBOUND_TYPE_UNSPECIFIED: WorkerStreamOutboundType
WORKER_SERVICE_OUTBOUND_TYPE_REGISTER: WorkerStreamOutboundType
WORKER_SERVICE_OUTBOUND_TYPE_JOB_STATUS: WorkerStreamOutboundType
WORKER_SERVICE_OUTBOUND_TYPE_JOB_RESULT: WorkerStreamOutboundType
WORKER_SERVICE_OUTBOUND_TYPE_JOB_ERROR: WorkerStreamOutboundType

class WorkerStreamInbound(_message.Message):
    __slots__ = ("job", "command")
    JOB_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    job: JobAssignment
    command: ControlCommand
    def __init__(
        self,
        job: _Optional[_Union[JobAssignment, _Mapping]] = ...,
        command: _Optional[_Union[ControlCommand, _Mapping]] = ...,
    ) -> None: ...

class JobAssignment(_message.Message):
    __slots__ = ("job_id", "job_type", "function", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    job_type: _common_pb2.JobType
    function: _common_pb2.WorkflowFunction
    metadata: _containers.ScalarMap[str, str]
    def __init__(
        self,
        job_id: _Optional[str] = ...,
        job_type: _Optional[_Union[_common_pb2.JobType, str]] = ...,
        function: _Optional[_Union[_common_pb2.WorkflowFunction, _Mapping]] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class ControlCommand(_message.Message):
    __slots__ = ("type", "target", "params")
    class ParamsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    TYPE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    type: CommandType
    target: str
    params: _containers.ScalarMap[str, str]
    def __init__(
        self,
        type: _Optional[_Union[CommandType, str]] = ...,
        target: _Optional[str] = ...,
        params: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class WorkerStreamOutbound(_message.Message):
    __slots__ = ("worker_id", "type", "registration", "job", "result", "error")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    JOB_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    type: WorkerStreamOutboundType
    registration: WorkerRegistration
    job: _common_pb2.JobStatus
    result: _common_pb2.JobResult
    error: _common_pb2.JobError
    def __init__(
        self,
        worker_id: _Optional[str] = ...,
        type: _Optional[_Union[WorkerStreamOutboundType, str]] = ...,
        registration: _Optional[_Union[WorkerRegistration, _Mapping]] = ...,
        job: _Optional[_Union[_common_pb2.JobStatus, _Mapping]] = ...,
        result: _Optional[_Union[_common_pb2.JobResult, _Mapping]] = ...,
        error: _Optional[_Union[_common_pb2.JobError, _Mapping]] = ...,
    ) -> None: ...

class WorkerRegistration(_message.Message):
    __slots__ = ("worker_type", "capabilities")
    WORKER_TYPE_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    worker_type: str
    capabilities: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        worker_type: _Optional[str] = ...,
        capabilities: _Optional[_Iterable[str]] = ...,
    ) -> None: ...
