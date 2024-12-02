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

class WorkflowExecMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKFLOW_EXEC_MODE_UNSPECIFIED: _ClassVar[WorkflowExecMode]
    WORKFLOW_EXEC_MODE_SYNC: _ClassVar[WorkflowExecMode]
    WORKFLOW_EXEC_MODE_ASYNC: _ClassVar[WorkflowExecMode]
    WORKFLOW_EXEC_MODE_INTERACTIVE: _ClassVar[WorkflowExecMode]

class WorkflowCommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKFLOW_COMMAND_TYPE_UNSPECIFIED: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_RUN: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_PAUSE: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_RESUME: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_CANCEL: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_ABORT: _ClassVar[WorkflowCommandType]
    WORKFLOW_COMMAND_TYPE_LIST: _ClassVar[WorkflowCommandType]

class EventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_TYPE_UNSPECIFIED: _ClassVar[EventType]
    EVENT_TYPE_EXECUTION_QUEUED: _ClassVar[EventType]
    EVENT_TYPE_EXECUTION_STARTED: _ClassVar[EventType]
    EVENT_TYPE_EXECUTION_COMPLETED: _ClassVar[EventType]
    EVENT_TYPE_EXECUTION_FAILED: _ClassVar[EventType]
    EVENT_TYPE_WORKFLOW_STARTED: _ClassVar[EventType]
    EVENT_TYPE_WORKFLOW_COMPLETED: _ClassVar[EventType]
    EVENT_TYPE_WORKFLOW_FAILED: _ClassVar[EventType]
    EVENT_TYPE_TASK_STARTED: _ClassVar[EventType]
    EVENT_TYPE_TASK_COMPLETED: _ClassVar[EventType]
    EVENT_TYPE_TASK_FAILED: _ClassVar[EventType]
    EVENT_TYPE_AGENT_STARTED: _ClassVar[EventType]
    EVENT_TYPE_AGENT_COMPLETED: _ClassVar[EventType]
    EVENT_TYPE_AGENT_FAILED: _ClassVar[EventType]
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
WORKFLOW_EXEC_MODE_UNSPECIFIED: WorkflowExecMode
WORKFLOW_EXEC_MODE_SYNC: WorkflowExecMode
WORKFLOW_EXEC_MODE_ASYNC: WorkflowExecMode
WORKFLOW_EXEC_MODE_INTERACTIVE: WorkflowExecMode
WORKFLOW_COMMAND_TYPE_UNSPECIFIED: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_RUN: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_PAUSE: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_RESUME: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_CANCEL: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_ABORT: WorkflowCommandType
WORKFLOW_COMMAND_TYPE_LIST: WorkflowCommandType
EVENT_TYPE_UNSPECIFIED: EventType
EVENT_TYPE_EXECUTION_QUEUED: EventType
EVENT_TYPE_EXECUTION_STARTED: EventType
EVENT_TYPE_EXECUTION_COMPLETED: EventType
EVENT_TYPE_EXECUTION_FAILED: EventType
EVENT_TYPE_WORKFLOW_STARTED: EventType
EVENT_TYPE_WORKFLOW_COMPLETED: EventType
EVENT_TYPE_WORKFLOW_FAILED: EventType
EVENT_TYPE_TASK_STARTED: EventType
EVENT_TYPE_TASK_COMPLETED: EventType
EVENT_TYPE_TASK_FAILED: EventType
EVENT_TYPE_AGENT_STARTED: EventType
EVENT_TYPE_AGENT_COMPLETED: EventType
EVENT_TYPE_AGENT_FAILED: EventType

class InboundWorkerMessage(_message.Message):
    __slots__ = ("type", "request_id", "worker_id", "deployment_id", "metadata", "registration", "heartbeat", "workflow_status", "workflow_result", "list_workflows")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_RESULT_FIELD_NUMBER: _ClassVar[int]
    LIST_WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    type: InboundWorkerMessageType
    request_id: str
    worker_id: str
    deployment_id: str
    metadata: _containers.ScalarMap[str, str]
    registration: WorkerRegistration
    heartbeat: WorkerHeartbeat
    workflow_status: WorkflowStatus
    workflow_result: _common_pb2.WorkflowResult
    list_workflows: _common_pb2.ListWorkflowsResponse
    def __init__(self, type: _Optional[_Union[InboundWorkerMessageType, str]] = ..., request_id: _Optional[str] = ..., worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., registration: _Optional[_Union[WorkerRegistration, _Mapping]] = ..., heartbeat: _Optional[_Union[WorkerHeartbeat, _Mapping]] = ..., workflow_status: _Optional[_Union[WorkflowStatus, _Mapping]] = ..., workflow_result: _Optional[_Union[_common_pb2.WorkflowResult, _Mapping]] = ..., list_workflows: _Optional[_Union[_common_pb2.ListWorkflowsResponse, _Mapping]] = ...) -> None: ...

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
    __slots__ = ("type", "request_id", "worker_id", "deployment_id", "metadata", "workflow_command", "ack")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_COMMAND_FIELD_NUMBER: _ClassVar[int]
    ACK_FIELD_NUMBER: _ClassVar[int]
    type: OutboundWorkerMessageType
    request_id: str
    worker_id: str
    deployment_id: str
    metadata: _containers.ScalarMap[str, str]
    workflow_command: WorkflowCommand
    ack: WorkerAck
    def __init__(self, type: _Optional[_Union[OutboundWorkerMessageType, str]] = ..., request_id: _Optional[str] = ..., worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., workflow_command: _Optional[_Union[WorkflowCommand, _Mapping]] = ..., ack: _Optional[_Union[WorkerAck, _Mapping]] = ...) -> None: ...

class WorkerAck(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class WorkflowCommand(_message.Message):
    __slots__ = ("type", "metadata", "run_workflow", "pause_workflow", "resume_workflow", "cancel_workflow", "abort_workflow", "list_workflows")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    RUN_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    PAUSE_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    RESUME_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    CANCEL_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    ABORT_WORKFLOW_FIELD_NUMBER: _ClassVar[int]
    LIST_WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    type: WorkflowCommandType
    metadata: _containers.ScalarMap[str, str]
    run_workflow: RunWorkflowCommand
    pause_workflow: PauseWorkflowCommand
    resume_workflow: ResumeWorkflowCommand
    cancel_workflow: CancelWorkflowCommand
    abort_workflow: AbortWorkflowCommand
    list_workflows: ListWorkflowsCommand
    def __init__(self, type: _Optional[_Union[WorkflowCommandType, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., run_workflow: _Optional[_Union[RunWorkflowCommand, _Mapping]] = ..., pause_workflow: _Optional[_Union[PauseWorkflowCommand, _Mapping]] = ..., resume_workflow: _Optional[_Union[ResumeWorkflowCommand, _Mapping]] = ..., cancel_workflow: _Optional[_Union[CancelWorkflowCommand, _Mapping]] = ..., abort_workflow: _Optional[_Union[AbortWorkflowCommand, _Mapping]] = ..., list_workflows: _Optional[_Union[ListWorkflowsCommand, _Mapping]] = ...) -> None: ...

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

class ExecutionEventData(_message.Message):
    __slots__ = ("execution_id", "status", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    status: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, execution_id: _Optional[str] = ..., status: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class WorkflowEventData(_message.Message):
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

class TaskEventData(_message.Message):
    __slots__ = ("task_id", "workflow_id", "status", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    workflow_id: str
    status: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, task_id: _Optional[str] = ..., workflow_id: _Optional[str] = ..., status: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RuntimeExecutionEventRequest(_message.Message):
    __slots__ = ("event_id", "event_type", "timestamp", "workflow_event", "task_event")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_EVENT_FIELD_NUMBER: _ClassVar[int]
    TASK_EVENT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    event_type: EventType
    timestamp: int
    workflow_event: WorkflowEventData
    task_event: TaskEventData
    def __init__(self, event_id: _Optional[str] = ..., event_type: _Optional[_Union[EventType, str]] = ..., timestamp: _Optional[int] = ..., workflow_event: _Optional[_Union[WorkflowEventData, _Mapping]] = ..., task_event: _Optional[_Union[TaskEventData, _Mapping]] = ...) -> None: ...

class RuntimeExecutionEventResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class RegisterWorkerRequest(_message.Message):
    __slots__ = ("worker_id", "deployment_id", "workflows")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    deployment_id: str
    workflows: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., workflows: _Optional[_Iterable[str]] = ...) -> None: ...

class RegisterWorkerResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
