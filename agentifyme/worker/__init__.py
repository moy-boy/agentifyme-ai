import json
import os
import time
import traceback
from typing import Any, get_type_hints

import orjson
from loguru import logger
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel

from agentifyme import __version__
from agentifyme.components.workflow import WorkflowConfig
from agentifyme.errors import AgentifyMeError
from agentifyme.worker.callback import CallbackHandler
from agentifyme.worker.helpers import build_args_from_signature
from agentifyme.worker.telemetry import (
    auto_instrument,
    setup_telemetry,
)

tracer = trace.get_tracer(__name__)


def initialize():
    initialize_sentry()
    agentifyme_env = os.getenv("AGENTIFYME_ENV")
    agentifyme_project_dir = os.getenv("AGENTIFYME_PROJECT_DIR")
    otel_endpoint = os.getenv("AGENTIFYME_OTEL_ENDPOINT", "gw.agentifyme.ai:3418")
    logger.info(f"OTEL Endpoint: {otel_endpoint}")

    callback_handler = CallbackHandler()

    # Setup telemetry
    setup_telemetry(
        otel_endpoint,
        agentifyme_env,
        __version__,
    )

    # Add instrumentation to workflows and tasks
    auto_instrument(agentifyme_project_dir, callback_handler)


def initialize_sentry():
    """Initialize Sentry for error tracking"""
    enable_telemetry = os.getenv("AGENTIFYME_ENABLE_TELEMETRY")
    sentry_dsn = os.getenv("AGENTIFYME_SENTRY_DSN")
    environment = os.getenv("AGENTIFYME_ENV")
    if enable_telemetry and sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            release=str(__version__),
            environment=environment,
            send_default_pii=False,
            attach_stacktrace=True,
            enable_tracing=True,
            propagate_traces=True,
        )


def execute_fn(name: str, input: str, trace_context: str) -> bytes:
    """Execute a workflow"""

    logger.info(f"Executing workflow {name} with input {input}")
    worker_id = os.getenv("AGENTIFYME_WORKER_ID")
    logger.info(f"Worker ID: {worker_id}")
    deployment_id = os.getenv("AGENTIFYME_DEPLOYMENT_ID")
    logger.info(f"Deployment ID: {deployment_id}")
    project_id = os.getenv("AGENTIFYME_PROJECT_ID")
    logger.info(f"Project ID: {project_id}")
    organization_id = os.getenv("AGENTIFYME_ORGANIZATION_ID")
    logger.info(f"Organization ID: {organization_id}")

    # Parse the trace context
    try:
        context_data = json.loads(trace_context)
        traceparent = context_data.get("traceparent", "")
        baggage = context_data.get("baggage", "")

        # Create carrier for OpenTelemetry
        carrier = {}
        if traceparent:
            carrier["traceparent"] = traceparent
        if baggage:
            carrier["baggage"] = baggage
    except:
        carrier = {}

    # Extract context
    from opentelemetry.propagate import extract

    ctx = extract(carrier)

    with tracer.start_as_current_span("workflow.run", context=ctx) as span:
        start_time = time.perf_counter()
        try:
            parsed_input = orjson.loads(input)

            _workflow = WorkflowConfig.get(name)
            _workflow_config = _workflow.config

            func_args = build_args_from_signature(_workflow_config.func, parsed_input)
            output = _workflow_config.func(**func_args)
            return_type = get_type_hints(_workflow_config.func).get("return")
            return_type_str = str(return_type.__name__) if return_type else None

            output_data = _process_output(output, return_type)

            if return_type_str is None:
                return_type_str = type(output_data).__name__

            output_data_json = orjson.dumps({"status": "success", "data": output_data, "return_type": return_type_str})
            span.set_attribute("output", str(output_data_json))
            span.set_status(Status(StatusCode.OK))
            end_time = time.perf_counter()
            span.set_attribute("execution_time", end_time - start_time)
            return output_data_json

        except Exception as e:
            traceback.print_exc()

            is_agentify_error = isinstance(e, AgentifyMeError)
            tb = traceback.format_exc()
            if not is_agentify_error:
                e = AgentifyMeError(
                    message=f"Error executing workflow {name}: {e}",
                    error_type=str(type(e).__name__),
                    tb=tb,
                )
            if is_agentify_error:
                error_dict = e.__dict__() if hasattr(e, "__dict__") else {}
                error_dict = {k: v for k, v in error_dict.items() if not callable(v) and not k.startswith("__")}
            else:
                error_dict = {"message": str(e), "error_type": type(e).__name__, "traceback": tb}

            error_data = orjson.dumps({"status": "error", "error": error_dict})
            error_message = str(e)

            span.set_attribute("error", str(error_data))
            span.set_status(Status(StatusCode.ERROR, error_message))
            return error_data


async def execute_fn_async(name: str, input: str, trace_context: str) -> bytes:
    """Execute a workflow asynchronously"""

    # Parse the trace context
    try:
        context_data = json.loads(trace_context)
        traceparent = context_data.get("traceparent", "")
        baggage = context_data.get("baggage", "")

        # Create carrier for OpenTelemetry
        carrier = {}
        if traceparent:
            carrier["traceparent"] = traceparent
        if baggage:
            carrier["baggage"] = baggage
    except:
        carrier = {}

    # Extract context
    from opentelemetry.propagate import extract

    ctx = extract(carrier)

    with tracer.start_as_current_span("workflow.run", context=ctx) as span:
        start_time = time.perf_counter()
        try:
            parsed_input = orjson.loads(input)

            _workflow = WorkflowConfig.get(name)
            _workflow_config = _workflow.config

            func_args = build_args_from_signature(_workflow_config.func, parsed_input)
            output = await _workflow_config.func(**func_args)
            return_type = get_type_hints(_workflow_config.func).get("return")
            return_type_str = str(return_type.__name__) if return_type else None

            output_data = _process_output(output, return_type)

            if return_type_str is None:
                return_type_str = type(output_data).__name__

            output_data_json = orjson.dumps({"status": "success", "data": output_data, "return_type": return_type_str})
            span.set_attribute("output", str(output_data_json))
            span.set_status(Status(StatusCode.OK))
            end_time = time.perf_counter()
            span.set_attribute("execution_time", end_time - start_time)
            return output_data_json

        except Exception as e:
            traceback.print_exc()

            is_agentify_error = isinstance(e, AgentifyMeError)

            tb = traceback.format_exc()

            if not is_agentify_error:
                e = AgentifyMeError(
                    message=f"Error executing workflow {name}: {e}",
                    error_type=str(type(e).__name__),
                    tb=tb,
                )

            if is_agentify_error:
                error_dict = e.__dict__() if hasattr(e, "__dict__") else {}
                error_dict = {k: v for k, v in error_dict.items() if not callable(v) and not k.startswith("__")}
            else:
                error_dict = {"message": str(e), "error_type": type(e).__name__, "traceback": tb}

            error_data = orjson.dumps({"status": "error", "error": error_dict})
            error_message = str(e)

            span.set_attribute("error", str(error_data))
            span.set_status(Status(StatusCode.ERROR, error_message))
            return error_data


def _process_output(result: Any, return_type: type) -> dict[str, Any]:
    """Process workflow output to ensure it's a valid JSON-serializable dictionary"""
    if isinstance(result, BaseModel):
        return result.model_dump()

    if isinstance(result, dict):
        if hasattr(return_type, "model_validate"):
            validated = return_type.model_validate(result)
            return validated.model_dump()
        return result
    if isinstance(result, str):
        return result

    if hasattr(return_type, "model_validate"):
        validated = return_type.model_validate(result)
        return validated.model_dump()

    raise ValueError(f"Unsupported output type: {type(result)}")
