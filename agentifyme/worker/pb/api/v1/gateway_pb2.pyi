from agentifyme.worker.pb.api.v1 import common_pb2 as _common_pb2
from google.api import annotations_pb2 as _annotations_pb2
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
    INBOUND_WORKER_MESSAGE_TYPE_REGISTRATION: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_RUNTIME_EVENT: _ClassVar[InboundWorkerMessageType]
    INBOUND_WORKER_MESSAGE_TYPE_WORKER_STATUS: _ClassVar[InboundWorkerMessageType]

class RuntimeEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RUNTIME_EVENT_TYPE_UNSPECIFIED: _ClassVar[RuntimeEventType]
    RUNTIME_EVENT_TYPE_EXECUTION: _ClassVar[RuntimeEventType]
    RUNTIME_EVENT_TYPE_WORKFLOW: _ClassVar[RuntimeEventType]
    RUNTIME_EVENT_TYPE_TASK: _ClassVar[RuntimeEventType]
    RUNTIME_EVENT_TYPE_LLM: _ClassVar[RuntimeEventType]

class RuntimeEventStage(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RUNTIME_EVENT_STAGE_UNSPECIFIED: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_INITIATED: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_QUEUED: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_STARTED: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_COMPLETED: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_CANCELLED: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_TIMEOUT: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_RETRY: _ClassVar[RuntimeEventStage]
    RUNTIME_EVENT_STAGE_FINISHED: _ClassVar[RuntimeEventStage]

class RuntimeEventStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RUNTIME_EVENT_STATUS_UNSPECIFIED: _ClassVar[RuntimeEventStatus]
    RUNTIME_EVENT_STATUS_SUCCESS: _ClassVar[RuntimeEventStatus]
    RUNTIME_EVENT_STATUS_FAILED: _ClassVar[RuntimeEventStatus]

class DataFormat(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DATA_FORMAT_UNSPECIFIED: _ClassVar[DataFormat]
    DATA_FORMAT_JSON: _ClassVar[DataFormat]
    DATA_FORMAT_BINARY: _ClassVar[DataFormat]
    DATA_FORMAT_STRUCT: _ClassVar[DataFormat]
    DATA_FORMAT_STRING: _ClassVar[DataFormat]

class WorkerState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKER_STATE_UNSPECIFIED: _ClassVar[WorkerState]
    WORKER_STATE_READY: _ClassVar[WorkerState]
    WORKER_STATE_BUSY: _ClassVar[WorkerState]
    WORKER_STATE_DRAINING: _ClassVar[WorkerState]

class OutboundWorkerMessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_ACK: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_REQUEST: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_COMMAND: _ClassVar[OutboundWorkerMessageType]
    OUTBOUND_WORKER_MESSAGE_TYPE_HEALTH_CHECK: _ClassVar[OutboundWorkerMessageType]

class ControlCommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTROL_COMMAND_TYPE_UNSPECIFIED: _ClassVar[ControlCommandType]
    CONTROL_COMMAND_TYPE_PAUSE: _ClassVar[ControlCommandType]
    CONTROL_COMMAND_TYPE_RESUME: _ClassVar[ControlCommandType]
    CONTROL_COMMAND_TYPE_CANCEL: _ClassVar[ControlCommandType]

class WorkflowExecMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKFLOW_EXEC_MODE_UNSPECIFIED: _ClassVar[WorkflowExecMode]
    WORKFLOW_EXEC_MODE_SYNC: _ClassVar[WorkflowExecMode]
    WORKFLOW_EXEC_MODE_ASYNC: _ClassVar[WorkflowExecMode]
    WORKFLOW_EXEC_MODE_INTERACTIVE: _ClassVar[WorkflowExecMode]
INBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_REGISTRATION: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_RUNTIME_EVENT: InboundWorkerMessageType
INBOUND_WORKER_MESSAGE_TYPE_WORKER_STATUS: InboundWorkerMessageType
RUNTIME_EVENT_TYPE_UNSPECIFIED: RuntimeEventType
RUNTIME_EVENT_TYPE_EXECUTION: RuntimeEventType
RUNTIME_EVENT_TYPE_WORKFLOW: RuntimeEventType
RUNTIME_EVENT_TYPE_TASK: RuntimeEventType
RUNTIME_EVENT_TYPE_LLM: RuntimeEventType
RUNTIME_EVENT_STAGE_UNSPECIFIED: RuntimeEventStage
RUNTIME_EVENT_STAGE_INITIATED: RuntimeEventStage
RUNTIME_EVENT_STAGE_QUEUED: RuntimeEventStage
RUNTIME_EVENT_STAGE_STARTED: RuntimeEventStage
RUNTIME_EVENT_STAGE_COMPLETED: RuntimeEventStage
RUNTIME_EVENT_STAGE_CANCELLED: RuntimeEventStage
RUNTIME_EVENT_STAGE_TIMEOUT: RuntimeEventStage
RUNTIME_EVENT_STAGE_RETRY: RuntimeEventStage
RUNTIME_EVENT_STAGE_FINISHED: RuntimeEventStage
RUNTIME_EVENT_STATUS_UNSPECIFIED: RuntimeEventStatus
RUNTIME_EVENT_STATUS_SUCCESS: RuntimeEventStatus
RUNTIME_EVENT_STATUS_FAILED: RuntimeEventStatus
DATA_FORMAT_UNSPECIFIED: DataFormat
DATA_FORMAT_JSON: DataFormat
DATA_FORMAT_BINARY: DataFormat
DATA_FORMAT_STRUCT: DataFormat
DATA_FORMAT_STRING: DataFormat
WORKER_STATE_UNSPECIFIED: WorkerState
WORKER_STATE_READY: WorkerState
WORKER_STATE_BUSY: WorkerState
WORKER_STATE_DRAINING: WorkerState
OUTBOUND_WORKER_MESSAGE_TYPE_UNSPECIFIED: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_ACK: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_REQUEST: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_COMMAND: OutboundWorkerMessageType
OUTBOUND_WORKER_MESSAGE_TYPE_HEALTH_CHECK: OutboundWorkerMessageType
CONTROL_COMMAND_TYPE_UNSPECIFIED: ControlCommandType
CONTROL_COMMAND_TYPE_PAUSE: ControlCommandType
CONTROL_COMMAND_TYPE_RESUME: ControlCommandType
CONTROL_COMMAND_TYPE_CANCEL: ControlCommandType
WORKFLOW_EXEC_MODE_UNSPECIFIED: WorkflowExecMode
WORKFLOW_EXEC_MODE_SYNC: WorkflowExecMode
WORKFLOW_EXEC_MODE_ASYNC: WorkflowExecMode
WORKFLOW_EXEC_MODE_INTERACTIVE: WorkflowExecMode

class InboundWorkerMessage(_message.Message):
    __slots__ = ("msg_id", "worker_id", "deployment_id", "timestamp", "metadata", "type", "registration", "event", "worker_status")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    WORKER_STATUS_FIELD_NUMBER: _ClassVar[int]
    msg_id: str
    worker_id: str
    deployment_id: str
    timestamp: int
    metadata: _containers.ScalarMap[str, str]
    type: InboundWorkerMessageType
    registration: WorkerRegistration
    event: RuntimeEvent
    worker_status: WorkerStatus
    def __init__(self, msg_id: _Optional[str] = ..., worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., metadata: _Optional[_Mapping[str, str]] = ..., type: _Optional[_Union[InboundWorkerMessageType, str]] = ..., registration: _Optional[_Union[WorkerRegistration, _Mapping]] = ..., event: _Optional[_Union[RuntimeEvent, _Mapping]] = ..., worker_status: _Optional[_Union[WorkerStatus, _Mapping]] = ...) -> None: ...

class WorkerRegistration(_message.Message):
    __slots__ = ("version", "capabilities")
    class CapabilitiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    version: str
    capabilities: _containers.ScalarMap[str, str]
    def __init__(self, version: _Optional[str] = ..., capabilities: _Optional[_Mapping[str, str]] = ...) -> None: ...

class LLMEventData(_message.Message):
    __slots__ = ("model", "vendor", "total_tokens", "prompt_tokens", "completion_tokens", "total_cost", "prompt_cost", "completion_cost", "latency_ms", "temperature", "max_tokens", "messages", "response")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    VENDOR_FIELD_NUMBER: _ClassVar[int]
    TOTAL_TOKENS_FIELD_NUMBER: _ClassVar[int]
    PROMPT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_TOKENS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COST_FIELD_NUMBER: _ClassVar[int]
    PROMPT_COST_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_COST_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    MAX_TOKENS_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    model: str
    vendor: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: str
    prompt_cost: str
    completion_cost: str
    latency_ms: int
    temperature: float
    max_tokens: int
    messages: _containers.RepeatedScalarFieldContainer[str]
    response: str
    def __init__(self, model: _Optional[str] = ..., vendor: _Optional[str] = ..., total_tokens: _Optional[int] = ..., prompt_tokens: _Optional[int] = ..., completion_tokens: _Optional[int] = ..., total_cost: _Optional[str] = ..., prompt_cost: _Optional[str] = ..., completion_cost: _Optional[str] = ..., latency_ms: _Optional[int] = ..., temperature: _Optional[float] = ..., max_tokens: _Optional[int] = ..., messages: _Optional[_Iterable[str]] = ..., response: _Optional[str] = ...) -> None: ...

class RuntimeEvent(_message.Message):
    __slots__ = ("event_type", "event_stage", "event_name", "timestamp", "event_id", "parent_event_id", "run_id", "request_id", "idempotency_key", "status", "retry_attempt", "error", "max_retries", "retry_delay", "metadata", "input_data_format", "json_input", "binary_input", "struct_input", "string_input", "output_data_format", "json_output", "binary_output", "struct_output", "string_output", "llm_output")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    EVENT_STAGE_FIELD_NUMBER: _ClassVar[int]
    EVENT_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RETRY_ATTEMPT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    MAX_RETRIES_FIELD_NUMBER: _ClassVar[int]
    RETRY_DELAY_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    INPUT_DATA_FORMAT_FIELD_NUMBER: _ClassVar[int]
    JSON_INPUT_FIELD_NUMBER: _ClassVar[int]
    BINARY_INPUT_FIELD_NUMBER: _ClassVar[int]
    STRUCT_INPUT_FIELD_NUMBER: _ClassVar[int]
    STRING_INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_FORMAT_FIELD_NUMBER: _ClassVar[int]
    JSON_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    BINARY_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    STRUCT_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    STRING_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    LLM_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    event_type: RuntimeEventType
    event_stage: RuntimeEventStage
    event_name: str
    timestamp: int
    event_id: str
    parent_event_id: str
    run_id: str
    request_id: str
    idempotency_key: str
    status: RuntimeEventStatus
    retry_attempt: int
    error: _common_pb2.AgentifyMeError
    max_retries: int
    retry_delay: int
    metadata: _containers.ScalarMap[str, str]
    input_data_format: DataFormat
    json_input: str
    binary_input: bytes
    struct_input: _struct_pb2.Struct
    string_input: str
    output_data_format: DataFormat
    json_output: str
    binary_output: bytes
    struct_output: _struct_pb2.Struct
    string_output: str
    llm_output: LLMEventData
    def __init__(self, event_type: _Optional[_Union[RuntimeEventType, str]] = ..., event_stage: _Optional[_Union[RuntimeEventStage, str]] = ..., event_name: _Optional[str] = ..., timestamp: _Optional[int] = ..., event_id: _Optional[str] = ..., parent_event_id: _Optional[str] = ..., run_id: _Optional[str] = ..., request_id: _Optional[str] = ..., idempotency_key: _Optional[str] = ..., status: _Optional[_Union[RuntimeEventStatus, str]] = ..., retry_attempt: _Optional[int] = ..., error: _Optional[_Union[_common_pb2.AgentifyMeError, _Mapping]] = ..., max_retries: _Optional[int] = ..., retry_delay: _Optional[int] = ..., metadata: _Optional[_Mapping[str, str]] = ..., input_data_format: _Optional[_Union[DataFormat, str]] = ..., json_input: _Optional[str] = ..., binary_input: _Optional[bytes] = ..., struct_input: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., string_input: _Optional[str] = ..., output_data_format: _Optional[_Union[DataFormat, str]] = ..., json_output: _Optional[str] = ..., binary_output: _Optional[bytes] = ..., struct_output: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., string_output: _Optional[str] = ..., llm_output: _Optional[_Union[LLMEventData, _Mapping]] = ...) -> None: ...

class WorkerStatus(_message.Message):
    __slots__ = ("cpu_usage", "memory_usage", "disk_usage", "active_tasks", "state")
    CPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    DISK_USAGE_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_TASKS_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_tasks: int
    state: WorkerState
    def __init__(self, cpu_usage: _Optional[float] = ..., memory_usage: _Optional[float] = ..., disk_usage: _Optional[float] = ..., active_tasks: _Optional[int] = ..., state: _Optional[_Union[WorkerState, str]] = ...) -> None: ...

class OutboundWorkerMessage(_message.Message):
    __slots__ = ("msg_id", "timestamp", "metadata", "type", "workflow_request", "control_command", "health_check", "ack")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_REQUEST_FIELD_NUMBER: _ClassVar[int]
    CONTROL_COMMAND_FIELD_NUMBER: _ClassVar[int]
    HEALTH_CHECK_FIELD_NUMBER: _ClassVar[int]
    ACK_FIELD_NUMBER: _ClassVar[int]
    msg_id: str
    timestamp: int
    metadata: _containers.ScalarMap[str, str]
    type: OutboundWorkerMessageType
    workflow_request: WorkflowRequest
    control_command: ControlCommand
    health_check: HealthCheck
    ack: _common_pb2.MessageAck
    def __init__(self, msg_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., metadata: _Optional[_Mapping[str, str]] = ..., type: _Optional[_Union[OutboundWorkerMessageType, str]] = ..., workflow_request: _Optional[_Union[WorkflowRequest, _Mapping]] = ..., control_command: _Optional[_Union[ControlCommand, _Mapping]] = ..., health_check: _Optional[_Union[HealthCheck, _Mapping]] = ..., ack: _Optional[_Union[_common_pb2.MessageAck, _Mapping]] = ...) -> None: ...

class WorkflowRequest(_message.Message):
    __slots__ = ("run_id", "workflow_name", "idempotency_key", "metadata", "input_data_format", "json_input", "binary_input", "struct_input")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_NAME_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    INPUT_DATA_FORMAT_FIELD_NUMBER: _ClassVar[int]
    JSON_INPUT_FIELD_NUMBER: _ClassVar[int]
    BINARY_INPUT_FIELD_NUMBER: _ClassVar[int]
    STRUCT_INPUT_FIELD_NUMBER: _ClassVar[int]
    run_id: str
    workflow_name: str
    idempotency_key: str
    metadata: _containers.ScalarMap[str, str]
    input_data_format: DataFormat
    json_input: str
    binary_input: bytes
    struct_input: _struct_pb2.Struct
    def __init__(self, run_id: _Optional[str] = ..., workflow_name: _Optional[str] = ..., idempotency_key: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., input_data_format: _Optional[_Union[DataFormat, str]] = ..., json_input: _Optional[str] = ..., binary_input: _Optional[bytes] = ..., struct_input: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ControlCommand(_message.Message):
    __slots__ = ("type", "run_id", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    type: ControlCommandType
    run_id: str
    parameters: _containers.ScalarMap[str, str]
    def __init__(self, type: _Optional[_Union[ControlCommandType, str]] = ..., run_id: _Optional[str] = ..., parameters: _Optional[_Mapping[str, str]] = ...) -> None: ...

class HealthCheck(_message.Message):
    __slots__ = ("server_time",)
    SERVER_TIME_FIELD_NUMBER: _ClassVar[int]
    server_time: int
    def __init__(self, server_time: _Optional[int] = ...) -> None: ...

class SyncWorkflowsRequest(_message.Message):
    __slots__ = ("worker_id", "deployment_id", "workflows")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    WORKFLOWS_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    deployment_id: str
    workflows: _containers.RepeatedCompositeFieldContainer[_common_pb2.WorkflowConfig]
    def __init__(self, worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., workflows: _Optional[_Iterable[_Union[_common_pb2.WorkflowConfig, _Mapping]]] = ...) -> None: ...

class SyncWorkflowsResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class WorkerHeartbeatRequest(_message.Message):
    __slots__ = ("worker_id", "deployment_id", "status", "metadata", "metrics")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class MetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    deployment_id: str
    status: str
    metadata: _containers.ScalarMap[str, str]
    metrics: _containers.ScalarMap[str, int]
    def __init__(self, worker_id: _Optional[str] = ..., deployment_id: _Optional[str] = ..., status: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., metrics: _Optional[_Mapping[str, int]] = ...) -> None: ...

class WorkerHeartbeatResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
