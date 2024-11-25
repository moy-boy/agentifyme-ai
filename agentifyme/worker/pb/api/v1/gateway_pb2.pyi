from agentifyme.worker.pb.api.v1 import common_pb2 as _common_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InboundWorkerMessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_REGISTER: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_HEARTBEAT: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_STATUS: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_RESULT: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS: _ClassVar[InboundWorkerMessageType]

class OutboundWorkerMessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_ACK: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_COMMAND: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS: _ClassVar[OutboundWorkerMessageType]

class WorkflowCommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKFLOW_COMMAND_TYPE_UNSPECIFIED: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_RUN: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_PAUSE: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_RESUME: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_CANCEL: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_ABORT: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_LIST: _ClassVar[WorkflowCommandType]
INBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_REGISTER: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_HEARTBEAT: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_STATUS: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_RESULT: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS: InboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_ACK: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_COMMAND: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS: OutboundWorkerMessageType
WORKFLOW_COMMAND_TYPE_UNSPECIFIED: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_RUN: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_PAUSE: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_RESUME: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_CANCEL: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_ABORT: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_LIST: WorkflowCommandType

class InboundWorkerMessage(_message.Message):
    __slots__ = ("request_id", "worker_id", "deployment_id", "type", "registration", "heartbeat", "workflow_status", "workflow_result", "list_workflows")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_RESULT_FIELD_NUMBER: _ClassVar[int]
    LIST_WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    worker_id: str
    deployment_id: str
    type: InboundWorkerMessageType
    registration: WorkerRegistration
    heartbeat: WorkerHeartbeat
    workflow_status: WorkflowStatus
    workflow_result: _common_pb2.WorkflowResult
    list_workflows: _common_pb2.ListWorkflowsResponse
    def __init__(self, request_id: _Optional[str] = ..., worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., type: _Optional[_Union[InboundWorkerMessageType, str]] = ..., registration: _Optional[_Union[WorkerRegistration, _Mapping]] = ..., heartbeat: _Optional[_Union[WorkerHeartbeat, _Mapping]] = ..., workflow_status: _Optional[_Union[WorkflowStatus, _Mapping]] = ..., workflow_result: _Optional[_Union[_common_pb2.WorkflowResult, _Mapping]] = ..., list_workflows: _Optional[_Union[_common_pb2.ListWorkflowsResponse, _Mapping]] = ...) -> None: ...

class WorkerRegistration(_message.Message):
    __slots__ = ("workflows",)
    WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    workflows: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, workflows: _Optional[_Iterable[str]] = ...) -> None: ...

class WorkerHeartbeat(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class WorkflowStatus(_message.Message):
    __slots__ = ("workflow_id", "status", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    workflow_id: str
    status: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, workflow_id: _Optional[str] = ..., status: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class OutboundWorkerMessage(_message.Message):
    __slots__ = ("request_id", "worker_id", "deployment_id", "type", "workflow_command", "ack")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_COMMAND_FIELD_NUMBER: _ClassVar[int]
    ACK_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    worker_id: str
    deployment_id: str
    type: OutboundWorkerMessageType
    workflow_command: WorkflowCommand
    ack: WorkerAck
    def __init__(self, request_id: _Optional[str] = ..., worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., type: _Optional[_Union[OutboundWorkerMessageType, str]] = ..., workflow_command: _Optional[_Union[WorkflowCommand, _Mapping]] = ..., ack: _Optional[_Union[WorkerAck, _Mapping]] = ...) -> None: ...

class WorkerAck(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class WorkflowCommand(_message.Message):
    __slots__ = ("workflow_id", "type", "metadata", "requestor", "timestamp", "run_workflow", "pause_workflow", "resume_workflow", "cancel_workflow", "abort_workflow", "list_workflows")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    REQUESTOR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    RUN_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    PAUSE_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    RESUME_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    CANCEL_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    ABORT_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    LIST_WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    workflow_id: str
    type: WorkflowCommandType
    metadata: _containers.ScalarMap[str, str]
    requestor: str
    timestamp: int
    run_workflow: RunWorkflowCommand
    pause_workflow: PauseWorkflowCommand
    resume_workflow: ResumeWorkflowCommand
    cancel_workflow: CancelWorkflowCommand
    abort_workflow: AbortWorkflowCommand
    list_workflows: ListWorkflowsCommand
    def __init__(self, workflow_id: _Optional[str] = ..., type: _Optional[_Union[WorkflowCommandType, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., requestor: _Optional[str] = ..., timestamp: _Optional[int] = ..., run_workflow: _Optional[_Union[RunWorkflowCommand, _Mapping]] = ..., pause_workflow: _Optional[_Union[PauseWorkflowCommand, _Mapping]] = ..., resume_workflow: _Optional[_Union[ResumeWorkflowCommand, _Mapping]] = ..., cancel_workflow: _Optional[_Union[CancelWorkflowCommand, _Mapping]] = ..., abort_workflow: _Optional[_Union[AbortWorkflowCommand, _Mapping]] = ..., list_workflows: _Optional[_Union[ListWorkflowsCommand, _Mapping]] = ...) -> None: ...

class RunWorkflowCommand(_message.Message):
    __slots__ = ("workflow_name", "parameters")
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    workflow_name: str
    parameters: _struct_pb2.Struct
    def __init__(self, workflow_name: _Optional[str] = ..., parameters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class PauseWorkflowCommand(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResumeWorkflowCommand(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CancelWorkflowCommand(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AbortWorkflowCommand(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListWorkflowsCommand(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
