from enum import Enum
from typing import Final


class SpanType(str, Enum):
    API = "API"
    WORKFLOW = "WORKFLOW"
    TASK = "TASK"
    LLM = "LLM"
    EMBEDDING = "EMBEDDING"
    TOOL = "TOOL"
    MESSAGE = "MESSAGE"
    FUNCTION_CALL = "FUNCTION_CALL"
    NATS = "NATS"


class SemanticAttributes:
    # Span Type
    SPAN_TYPE: Final[str] = "span.type"

    # Service
    SERVICE_NAME: Final[str] = "service.name"
    SERVICE_VERSION: Final[str] = "service.version"
    SERVICE_ENV: Final[str] = "service.env"
    SERVICE_NAMESPACE: Final[str] = "service.namespace"
    SERVICE_INSTANCE_ID: Final[str] = "service.instance.id"

    # AgentifyMe Services
    API_SERVICE_NAME: Final[str] = "api"
    REQUEST_MANAGER_SERVICE_NAME: Final[str] = "request-manager"

    # User
    USER_ID: Final[str] = "user.id"

    # Session ID
    SESSION_ID: Final[str] = "session.id"

    # API
    API_REQUEST_ID: Final[str] = "api.request.id"
    API_REQUEST_METHOD: Final[str] = "api.request.method"
    API_REQUEST_URL: Final[str] = "api.request.url"
    API_REQUEST_ROUTE: Final[str] = "api.request.route"
    API_REQUEST_HEADERS: Final[str] = "api.request.headers"
    API_REQUEST_BODY: Final[str] = "api.request.body"
    API_RESPONSE_HEADERS: Final[str] = "api.response.headers"
    API_RESPONSE_BODY: Final[str] = "api.response.body"
    API_RESPONSE_STATUS_CODE: Final[str] = "api.response.status_code"

    # Organization
    ORGANIZATION_ID: Final[str] = "organization.id"
    ORGANIZATION_NAME: Final[str] = "organization.name"
    ORGANIZATION_REF: Final[str] = "organization.ref"

    # Project
    PROJECT_ID: Final[str] = "project.id"
    PROJECT_NAME: Final[str] = "project.name"
    PROJECT_REF: Final[str] = "project.ref"

    # Deployment
    DEPLOYMENT_ID: Final[str] = "deployment.id"
    DEPLOYMENT_NAME: Final[str] = "deployment.name"

    # Worker
    WORKER_ID: Final[str] = "worker.id"
    WORKER_ENDPOINT: Final[str] = "worker.endpoint"

    # Host
    HOST_ID: Final[str] = "host.id"
    HOST_NAME: Final[str] = "host.name"
    HOST_TYPE: Final[str] = "host.type"
    HOST_INFRA_TYPE: Final[str] = "host.infra_type"

    # Workflow
    WORKFLOW_ID: Final[str] = "workflow.id"
    WORKFLOW_NAME: Final[str] = "workflow.name"
    WORKFLOW_INVOCATION_PARAMETERS: Final[str] = "workflow.invocation_parameters"
    WORKFLOW_OUTPUT: Final[str] = "workflow.output"
    WORKFLOW_RUN_ID: Final[str] = "workflow.run.id"

    # Document
    DOCUMENT_ID: Final[str] = "document.id"
    DOCUMENT_TYPE: Final[str] = "document.type"
    DOCUMENT_CONTENT: Final[str] = "document.content"
    DOCUMENT_METADATA: Final[str] = "document.metadata"
    DOCUMENT_SCORE: Final[str] = "document.score"

    # Embeddings
    EMBEDDING_ID: Final[str] = "embedding.id"
    EMBEDDING_MODEL_NAME: Final[str] = "embedding.model_name"
    EMBEDDING_VECTOR: Final[str] = "embedding.vector"
    EMBEDDING_TEXT: Final[str] = "embedding.text"

    # LLM
    LLM_ROLE: Final[str] = "llm.role"
    LLM_FUNCTION_CALL: Final[str] = "llm.function_call"
    LLM_INVOCATION_PARAMETERS: Final[str] = "llm.invocation_parameters"
    LLM_INPUT_MESSAGES: Final[str] = "llm.input_messages"
    LLM_OUTPUT_MESSAGES: Final[str] = "llm.output_messages"
    LLM_OUTPUT_MESSAGE: Final[str] = "llm.output_message"
    LLM_PROVIDER: Final[str] = "llm.provider"
    LLM_MODEL_NAME: Final[str] = "llm.model_name"
    LLM_PROMPT_TEMPLATE: Final[str] = "llm.prompt_template.template"
    LLM_PROMPT_TEMPLATE_VARIABLES: Final[str] = "llm.prompt_template.variables"
    LLM_PROMPT_TEMPLATE_VERSION: Final[str] = "llm.prompt_template.version"
    LLM_TOKEN_COUNT_COMPLETION: Final[str] = "llm.token_count.completion"
    LLM_TOKEN_COUNT_PROMPT: Final[str] = "llm.token_count.prompt"
    LLM_TOKEN_COUNT_TOTAL: Final[str] = "llm.token_count.total"
    LLM_TOOLS: Final[str] = "llm.tools"
    LLM_SYSTEM: Final[str] = "llm.system"

    # Message
    MESSAGE_CONTENT: Final[str] = "message.content"
    MESSAGE_CONTENT_TYPE: Final[str] = "message.content_type"
    MESSAGE_ROLE: Final[str] = "message.role"
    MESSAGE_FUNCTION_CALL_ARGUMENTS: Final[str] = "message.function_call.arguments"
    MESSAGE_FUNCTION_CALL_NAME: Final[str] = "message.function_call.name"
    MESSAGE_TOOL_CALLS: Final[str] = "message.tool_calls"
    MESSAGE_TOOL_CALL_ID: Final[str] = "message.tool_call.id"
    MESSAGE_TOOL_CALL_NAME: Final[str] = "message.tool_call.name"
    MESSAGE_TOOL_CALL_ARGUMENTS: Final[str] = "message.tool_call.arguments"
