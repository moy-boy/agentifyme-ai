import asyncio
import os
import time
from datetime import datetime

import orjson
import wrapt
from loguru import logger
from opentelemetry import baggage, context, trace
from opentelemetry.context import attach, detach
from opentelemetry.trace import SpanKind, Status, StatusCode
from pydantic import BaseModel

from agentifyme.components.task import TaskConfig
from agentifyme.components.workflow import WorkflowConfig
from agentifyme.utilities.modules import load_modules_from_directory
from agentifyme.worker.callback import CallbackHandler
from agentifyme.worker.telemetry.semconv import SemanticAttributes

from .base import get_resource_attributes


# Custom processor to add trace info
def add_trace_info(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span:
        ctx = context.get_current()
        trace_id = trace.get_current_span(ctx).get_span_context().trace_id
        span_id = trace.get_current_span(ctx).get_span_context().span_id
        event_dict["trace_id"] = f"{trace_id:032x}"
        event_dict["span_id"] = f"{span_id:016x}"
    return event_dict


def add_context_attributes(logger, method_name, event_dict):
    attributes = get_resource_attributes()
    for key, value in attributes.items():
        event_dict[key] = value
    return event_dict


def rename_event_to_message(logger, method_name, event_dict):
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def get_base_attributes():
    """Get common base attributes for instrumentation"""
    return {
        SemanticAttributes.PROJECT_ID: os.getenv("AGENTIFYME_PROJECT_ID", "UNKNOWN"),
        SemanticAttributes.DEPLOYMENT_ID: os.getenv("AGENTIFYME_DEPLOYMENT_ID", "UNKNOWN"),
        SemanticAttributes.WORKER_ID: os.getenv("AGENTIFYME_REPLICA_ID", "UNKNOWN"),
        SemanticAttributes.DEPLOYMENT_NAME: os.getenv("AGENTIFYME_ENDPOINT", "UNKNOWN"),
    }


def prepare_span_attributes(span, span_name):
    """Prepare common span attributes"""
    trace_id = format(span.get_span_context().trace_id, "032x")
    span_id = format(span.get_span_context().span_id, "016x")
    request_id = baggage.get_baggage("request.id")

    span.set_attribute("request.id", request_id)

    return {
        "name": span_name,
        "request.id": request_id,
        "trace.id": trace_id,
        "step_id": span_id,
        "parent_id": baggage.get_baggage("parent_id"),
        "timestamp": int(datetime.now().timestamp() * 1_000_000),
        **get_base_attributes(),
    }


def prepare_output(output):
    """Standardize output preparation"""
    if isinstance(output, dict):
        return {k: v for k, v in output.items() if k != "output"}
    if isinstance(output, BaseModel):
        return output.model_dump()
    if isinstance(output, object):
        return orjson.dumps(output)
    return str(output)


def create_instrumentation_wrapper(callback_handler: CallbackHandler, event_source: str, name: str):
    """Create an instrumentation wrapper with the given callback handler and event source"""

    def instrument_function(wrapped, instance, args, kwargs):
        """Core instrumentation logic"""
        tracer = trace.get_tracer("agentifyme-worker")

        async def async_handler():
            start_time = time.perf_counter()
            span_name = wrapped.__name__

            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.INTERNAL,
                attributes=get_base_attributes(),
            ) as span:
                attributes = prepare_span_attributes(span, span_name)
                token = attach(baggage.set_baggage("parent_id", attributes["step_id"]))

                try:
                    _kwargs = kwargs.copy()
                    _kwargs.update(zip(wrapped.__code__.co_varnames, args, strict=False))
                    await callback_handler.fire_event_async(f"{event_source}.run", "started", {**attributes, "name": name, "input": _kwargs})
                    output = await wrapped(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    prepared_output = prepare_output(output)
                    await callback_handler.fire_event_async(f"{event_source}.run", "completed", {**attributes, "name": name, "output": prepared_output, "input": _kwargs})
                    return output

                except Exception as error:
                    logger.error(f"Operation failed - {span_name}", exc_info=True)
                    span.record_exception(error)
                    span.set_status(Status(StatusCode.ERROR, str(error)))
                    await callback_handler.fire_event_async(f"{event_source}.run", "completed", {**attributes, "name": name, "error": str(error), "input": _kwargs})
                    raise

                finally:
                    span.set_attribute("duration", time.perf_counter() - start_time)
                    detach(token)

        def sync_handler():
            start_time = time.perf_counter()
            span_name = wrapped.__name__

            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.INTERNAL,
                attributes=get_base_attributes(),
            ) as span:
                attributes = prepare_span_attributes(span, span_name)
                token = attach(baggage.set_baggage("parent_id", attributes["step_id"]))

                try:
                    _kwargs = kwargs.copy()
                    _kwargs.update(zip(wrapped.__code__.co_varnames, args, strict=False))
                    callback_handler.fire_event(f"{event_source}.run", "started", {**attributes, "name": name, "input": _kwargs})

                    output = wrapped(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    prepared_output = prepare_output(output)
                    callback_handler.fire_event(f"{event_source}.run", "completed", {**attributes, "name": name, "output": prepared_output, "input": _kwargs})
                    return output

                except Exception as error:
                    logger.error(f"Operation failed - {span_name}", exc_info=True)
                    span.record_exception(error)
                    span.set_status(Status(StatusCode.ERROR, str(error)))
                    callback_handler.fire_event(f"{event_source}.run", "completed", {**attributes, "name": name, "error": str(error), "input": _kwargs})
                    raise

                finally:
                    span.set_attribute("duration", time.perf_counter() - start_time)
                    detach(token)

        if asyncio.iscoroutinefunction(wrapped):
            return async_handler()
        return sync_handler()

    return instrument_function


class OTELInstrumentor:
    @staticmethod
    def instrument(project_dir: str, callback_handler: CallbackHandler):
        if os.path.exists(os.path.join(project_dir, "src")):
            project_dir = os.path.join(project_dir, "src")

        logger.info(f"Loading workflows and tasks from project directory - {project_dir}")

        try:
            load_modules_from_directory(project_dir)

            # Instrument tasks
            for task_name, task in TaskConfig.get_registry().items():
                task_wrapper = create_instrumentation_wrapper(callback_handler, "task", task_name)
                wrapt.wrap_function_wrapper(task.config.func.__module__, task.config.func.__name__, task_wrapper)

            # Instrument workflows
            for workflow_name, workflow in WorkflowConfig._registry.items():
                workflow_wrapper = create_instrumentation_wrapper(callback_handler, "workflow", workflow_name)
                wrapt.wrap_function_wrapper(workflow.config.func.__module__, workflow.config.func.__name__, workflow_wrapper)

        except ValueError as e:
            logger.error(f"Error loading modules from {project_dir}: {e}", exc_info=True)
            raise
