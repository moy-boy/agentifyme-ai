import os
import traceback
from typing import Any, get_type_hints

import orjson
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


def initialize():
    initialize_sentry()
    agentifyme_env = os.getenv("AGENTIFYME_ENV")
    agentifyme_project_dir = os.getenv("AGENTIFYME_PROJECT_DIR")
    otel_endpoint = os.getenv("AGENTIFYME_OTEL_ENDPOINT", "5.78.99.34:4317")
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


def execute_fn(name: str, input: str) -> bytes:
    """Execute a workflow"""
    try:
        input = orjson.loads(input)
        _workflow = WorkflowConfig.get(name)
        _workflow_config = _workflow.config
        func_args = build_args_from_signature(_workflow_config.func, input)

        output = _workflow_config.func(**func_args)

        return_type = get_type_hints(_workflow_config.func).get("return")
        output_data = _process_output(output, return_type)
        data_info = {"status": "success", "data": output_data}

        return orjson.dumps(data_info)

    except AgentifyMeError as e:
        error_info = {"status": "error", "error": e.__dict__()}
        return orjson.dumps(error_info)

    except Exception as e:
        agentifyme_error = AgentifyMeError(
            message=f"Error executing workflow {name}: {e}",
            error_type=type(e),
            tb=traceback.format_exc(),
        )
        error_info = {"status": "error", "error": agentifyme_error.__dict__()}
        return orjson.dumps(error_info)


async def execute_fn_async(name: str, input: str) -> bytes:
    """Execute a workflow asynchronously"""
    try:
        input = orjson.loads(input)
        _workflow = WorkflowConfig.get(name)
        _workflow_config = _workflow.config
        func_args = build_args_from_signature(_workflow_config.func, input)
        output = await _workflow_config.func(**func_args)

        return_type = get_type_hints(_workflow_config.func).get("return")
        output_data = _process_output(output, return_type)

        data_info = {"status": "success", "data": output_data}
        output_data_json = orjson.dumps(data_info)
        return output_data_json

    except AgentifyMeError as e:
        error_info = {"status": "error", "error": e.__dict__()}
        return orjson.dumps(error_info)

    except Exception as e:
        agentifyme_error = AgentifyMeError(
            message=f"Error executing workflow {name}: {e}",
            error_type=type(e),
            tb=traceback.format_exc(),
        )
        error_info = {"status": "error", "error": agentifyme_error.__dict__()}
        return orjson.dumps(error_info)


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
