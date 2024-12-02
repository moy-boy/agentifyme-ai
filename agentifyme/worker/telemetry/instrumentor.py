import asyncio
import json
import os
import socket
import time
import traceback

import wrapt
from loguru import logger
from opentelemetry import context, trace
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import SpanKind, Status, StatusCode
from pydantic import BaseModel

from agentifyme.tasks.task import TaskConfig
from agentifyme.utilities.modules import load_modules_from_directory
from agentifyme.worker.telemetry.semconv import SemanticAttributes
from agentifyme.workflows.workflow import WorkflowConfig

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


class InstrumentationWrapper(wrapt.ObjectProxy):
    tracer = trace.get_tracer("agentifyme-worker")

    def get_attributes(self):
        project_id = os.getenv("AGENTIFYME_PROJECT_ID", default="UNKNOWN")
        deployment_id = os.getenv("AGENTIFYME_DEPLOYMENT_ID", default="UNKNOWN")
        replica_id = os.getenv("AGENTIFYME_REPLICA_ID", default="UNKNOWN")
        endpoint = os.getenv("AGENTIFYME_ENDPOINT", default="UNKNOWN")
        return {
            SemanticAttributes.PROJECT_ID: project_id,
            SemanticAttributes.DEPLOYMENT_ID: deployment_id,
            SemanticAttributes.WORKER_ID: replica_id,
            SemanticAttributes.DEPLOYMENT_NAME: endpoint,
        }

    def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self.__wrapped__):
            return self._async_call(*args, **kwargs)
        else:
            return self._sync_call(*args, **kwargs)

    def _sync_call(self, *args, **kwargs):
        span_name = self.__wrapped__.__name__
        start_time = time.perf_counter()
        with self.tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.INTERNAL,
            attributes=self.get_attributes(),
        ) as span:
            output = None
            try:
                logger.info("Starting operation", operation=span_name)
                output = self.__wrapped__(*args, **kwargs)
                _log_output = self._prepare_log_output(output)
                logger.info("Operation completed successfully")
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                traceback.print_exc()
                logger.error("Operation failed", exc_info=True, error=str(e))
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise e
            finally:
                _output = self._prepare_log_output(output)
                # span.set_attribute("output", _output)
                end_time = time.perf_counter()
                ts_diff = end_time - start_time
                span.set_attribute("duration", ts_diff)
            return output

    async def _async_call(self, *args, **kwargs):
        span_name = self.__wrapped__.__name__
        start_time = time.perf_counter()

        with self.tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.INTERNAL,
            attributes=self.get_attributes(),
        ) as span:
            output = None

            try:
                logger.info("Starting operation", operation=span_name)
                output = await self.__wrapped__(*args, **kwargs)
                _log_output = self._prepare_log_output(output)
                logger.info("Operation completed successfully", result=_log_output)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                logger.error("Operation failed", exc_info=True, error=str(e))
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise e
            finally:
                span.set_attribute("output", output)
                end_time = time.perf_counter()
                ts_diff = end_time - start_time
                span.set_attribute("duration", ts_diff)

            return output

    def _prepare_log_output(self, output):
        if isinstance(output, dict):
            return {k: v for k, v in output.items() if k != "output"}
        elif isinstance(output, BaseModel):
            return output.model_dump()
        elif isinstance(output, object):
            return json.dumps(output)
        else:
            return str(output)


class OTELInstrumentor:
    @staticmethod
    def instrument(project_dir: str):
        WorkflowConfig.reset_registry()
        TaskConfig.reset_registry()

        # # if ./src exists, load modules from there
        if os.path.exists(os.path.join(project_dir, "src")):
            project_dir = os.path.join(project_dir, "src")

        logger.info(f"Loading workflows and tasks from project directory - {project_dir}")
        error = True
        try:
            load_modules_from_directory(project_dir)
            error = False
        except ValueError as e:
            logger.error(
                f"Error {e} while loading modules from project directory - {project_dir}",
                exc_info=True,
                error=str(e),
            )

        if error:
            logger.error("Failed to load modules, exiting")

        # Inject telemetry into tasks and workflows
        task_registry = TaskConfig.get_registry().copy()
        for task_name in TaskConfig.get_registry().keys():
            _task = TaskConfig.get_registry()[task_name]
            _task.config.func = InstrumentationWrapper(_task.config.func)
            task_registry[task_name] = _task
        TaskConfig._registry = task_registry

        workflow_registry = WorkflowConfig._registry.copy()
        for workflow_name in WorkflowConfig._registry.keys():
            _workflow = WorkflowConfig._registry[workflow_name]
            _workflow.config.func = InstrumentationWrapper(_workflow.config.func)
            workflow_registry[workflow_name] = _workflow
        WorkflowConfig._registry = workflow_registry

        logger.info("Found workflows", workflows=WorkflowConfig.get_all())

        # auto_instrument()


def auto_instrument():
    pass
