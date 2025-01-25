import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

import orjson
from opentelemetry import metrics, trace
from opentelemetry.baggage import get_baggage
from opentelemetry.trace import SpanKind, Status, StatusCode

from agentifyme.ml.llm import (
    LanguageModel,
    LanguageModelProvider,
    LanguageModelResponse,
)
from agentifyme.worker.callback import CallbackHandler
from agentifyme.worker.telemetry.semconv import SemanticAttributes, SpanType

from .semconv import SemanticAttributes

ResponseType = TypeVar("ResponseType", bound=LanguageModelResponse)

# Initialize provider-specific meters
meter = metrics.get_meter("agentifyme.llm")


# Request and duration metrics
request_duration = meter.create_histogram(
    "request.duration",
    description="Duration of LLM requests",
    unit="ms",
)

# Token count metrics using semantic convention names
total_tokens = meter.create_histogram(
    SemanticAttributes.LLM_TOKEN_COUNT_TOTAL,
    description="Total tokens used in LLM request and response",
    unit="tokens",
)
prompt_tokens = meter.create_histogram(
    SemanticAttributes.LLM_TOKEN_COUNT_PROMPT,
    description="Tokens used in LLM prompt",
    unit="tokens",
)
completion_tokens = meter.create_histogram(
    SemanticAttributes.LLM_TOKEN_COUNT_COMPLETION,
    description="Tokens used in LLM completion",
    unit="tokens",
)

# Error and request counters
errors = meter.create_counter(
    "errors.total",
    description="Total number of errors",
)
requests = meter.create_counter(
    "requests.total",
    description="Total number of requests",
)

# LLM metrics based on semantic conventions
tools = meter.create_counter(
    f"{SemanticAttributes.LLM_TOOLS}.total",
    description="Total number of tool definitions provided to LLM",
)
tool_calls = meter.create_counter(
    f"{SemanticAttributes.MESSAGE_TOOL_CALLS}.total",
    description="Number of tool calls in LLM responses",
)
function_calls = meter.create_counter(
    f"{SemanticAttributes.MESSAGE_FUNCTION_CALL_NAME}.total",
    description="Number of function calls in LLM responses",
)
model_usage = meter.create_histogram(
    f"{SemanticAttributes.LLM_MODEL_NAME}.usage",
    description="Usage metrics per model name",
)

# Model-specific attributes
latency = meter.create_histogram(
    f"{SemanticAttributes.LLM_PROVIDER}.latency",
    description="Latency by LLM provider",
    unit="ms",
)
result_errors = meter.create_counter(
    f"{SemanticAttributes.LLM_PROVIDER}.errors",
    description="Errors by LLM provider",
)


class LLMTelemetryContext:
    """Context manager for handling LLM telemetry across providers"""

    def __init__(self, method_name: str, provider: LanguageModelProvider):
        self.method_name = method_name
        self.provider = provider
        self.start_time = None
        self.tracer = trace.get_tracer("agentifyme-worker")

    @contextmanager
    def __call__(self, **attributes):
        with self.tracer.start_as_current_span(
            name=f"{self.provider.value}.{self.method_name}",
            kind=SpanKind.INTERNAL,
            attributes={SemanticAttributes.SPAN_TYPE: SpanType.LLM, "llm.provider": self.provider.value, **attributes},
        ) as span:
            self.start_time = time.monotonic()
            requests.add(1)

            try:
                yield span
            finally:
                if self.start_time:
                    duration_ms = (time.monotonic() - self.start_time) * 1000
                    request_duration.record(duration_ms, {"method": self.method_name})


def extract_telemetry_attributes(instance: LanguageModel, method_name: str, args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract telemetry attributes based on provider and method"""
    attributes = {}

    # Common attributes
    if hasattr(instance, "llm_model"):
        attributes[SemanticAttributes.LLM_MODEL_NAME] = instance.llm_model.value

    # # Get method signature and bind arguments

    if method_name == "generate":
        if len(args) > 0 and isinstance(args[0], list):
            messages = args[0]
            attributes[SemanticAttributes.LLM_INPUT_MESSAGES] = orjson.dumps([message.model_dump() for message in messages]).decode("utf-8")

    attributes[SemanticAttributes.LLM_INVOCATION_PARAMETERS] = orjson.dumps(kwargs).decode("utf-8")

    return attributes


def record_provider_metrics(provider: LanguageModelProvider, response: LanguageModelResponse, span: trace.Span) -> dict:
    """Record provider-specific metrics"""
    metrics = {}

    # Record token usage
    if response.usage:
        _total_tokens = response.usage.prompt_tokens + response.usage.completion_tokens
        prompt_tokens.record(response.usage.prompt_tokens)
        completion_tokens.record(response.usage.completion_tokens)
        total_tokens.record(_total_tokens)
        metrics[SemanticAttributes.LLM_TOKEN_COUNT_TOTAL] = _total_tokens
        metrics[SemanticAttributes.LLM_TOKEN_COUNT_PROMPT] = response.usage.prompt_tokens
        metrics[SemanticAttributes.LLM_TOKEN_COUNT_COMPLETION] = response.usage.completion_tokens

        span.set_attribute(SemanticAttributes.LLM_TOKEN_COUNT_TOTAL, _total_tokens)
        span.set_attribute(SemanticAttributes.LLM_TOKEN_COUNT_PROMPT, response.usage.prompt_tokens)
        span.set_attribute(SemanticAttributes.LLM_TOKEN_COUNT_COMPLETION, response.usage.completion_tokens)

    # Provider-specific metrics
    if provider == LanguageModelProvider.ANTHROPIC and response.tool_calls:
        tools.add(len(response.tool_calls))
        metrics[SemanticAttributes.LLM_TOOLS] = len(response.tool_calls)
    elif provider == LanguageModelProvider.OPENAI and response.tool_calls:
        function_calls.add(len(response.tool_calls))
        metrics[SemanticAttributes.MESSAGE_TOOL_CALLS] = len(response.tool_calls)

    return metrics


def llm_telemetry(method_name: str, callback_handler: CallbackHandler) -> Callable:
    """Decorator for adding telemetry to LLM methods"""

    def method_decorator(func: Callable[..., ResponseType]) -> Callable[..., ResponseType]:
        @wraps(func)
        def wrapper(instance: LanguageModel, *args, **kwargs) -> ResponseType:
            # Get provider from instance
            provider, _ = instance.get_model_name(instance.llm_model)

            with LLMTelemetryContext(method_name, provider)() as span:
                try:
                    trace_id = format(span.get_span_context().trace_id, "032x")
                    span_id = format(span.get_span_context().span_id, "016x")
                    parent_id = get_baggage("parent.id")
                    request_id = get_baggage("request.id")

                    attributes = {
                        "name": instance.llm_model.value,
                        "request.id": request_id,
                        "trace.id": trace_id,
                        "parent_id": parent_id,
                        "step_id": span_id,
                        "timestamp": int(datetime.now().timestamp() * 1_000_000),
                    }

                    # Set basic attributes
                    span.set_attributes(extract_telemetry_attributes(instance, method_name, args, kwargs))

                    callback_handler.on_llm_start(attributes)

                    # Execute method
                    result = func(instance, *args, **kwargs)

                    # Handle response
                    if isinstance(result, LanguageModelResponse):
                        if result.error:
                            result_errors.add(1)
                            span.record_exception(Exception(result.error))
                            span.set_status(Status(StatusCode.ERROR))
                        else:
                            metrics = record_provider_metrics(provider, result, span)
                            attributes.update(metrics)

                            span.set_status(Status(StatusCode.OK))
                            if result.message:
                                span.set_attribute(SemanticAttributes.LLM_OUTPUT_MESSAGE, result.message)

                    callback_handler.on_llm_end({**attributes, "output": result})
                    return result

                except Exception as e:
                    result_errors.add(1)
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    raise

        return wrapper

    return method_decorator


def llm_stream_telemetry(method_name: str, callback_handler: CallbackHandler) -> Callable:
    """Decorator for adding telemetry to streaming LLM methods"""

    def method_decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(instance: LanguageModel, *args, **kwargs):
            provider, _ = instance.get_model_name(instance.llm_model)

            with LLMTelemetryContext(method_name, provider)() as span:
                try:
                    span.set_attributes(extract_telemetry_attributes(instance, method_name, args, kwargs))

                    for chunk in func(instance, *args, **kwargs):
                        if isinstance(chunk, LanguageModelResponse):
                            if chunk.error:
                                result_errors.add(1)
                                span.record_exception(Exception(chunk.error))
                                span.set_status(Status(StatusCode.ERROR))
                            elif chunk.message:
                                span.set_attribute("response_chunk_length", len(chunk.message))
                        yield chunk

                except Exception as e:
                    result_errors.add(1)
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    raise

        return wrapper

    return method_decorator


def instrument_llm_class(cls: Any, callback_handler: CallbackHandler) -> None:
    """Instrument a Language Model class with telemetry"""
    methods = {
        "generate": llm_telemetry,
        "agenerate": llm_telemetry,
        "generate_stream": llm_stream_telemetry,
    }

    for method_name, decorator_factory in methods.items():
        if hasattr(cls, method_name):
            original_method = getattr(cls, method_name)
            decorated_method = decorator_factory(method_name, callback_handler)(original_method)
            setattr(cls, method_name, decorated_method)


def auto_instrument_language_models(callback_handler: CallbackHandler) -> None:
    """Automatically instrument all Language Model classes"""
    # import agentifyme.ml.llm

    # for provider in LanguageModelProvider:
    #     provider_module = getattr(agentifyme.ml.llm, provider.value.lower(), None)
    #     if provider_module:
    #         for name, obj in inspect.getmembers(provider_module):
    #             if isinstance(obj, type) and issubclass(obj, LanguageModel) and obj != LanguageModel:
    #                 instrument_llm_class(obj, callback_handler)
