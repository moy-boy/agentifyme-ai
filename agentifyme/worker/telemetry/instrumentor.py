import asyncio
import json
import os
import time
import traceback
from datetime import datetime

import wrapt
from loguru import logger
from opentelemetry import baggage, context, trace
from opentelemetry.context import attach, detach
from opentelemetry.trace import SpanKind, Status, StatusCode
from pydantic import BaseModel

from agentifyme.tasks.task import TaskConfig
from agentifyme.utilities.modules import load_modules_from_directory
from agentifyme.worker.callback import CallbackHandler
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

    def __init__(self, wrapped, callback_handler: CallbackHandler, event_source: str):
        super().__init__(wrapped)
        self.callback_handler = callback_handler
        self.event_source = event_source

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
            trace_id = format(span.get_span_context().trace_id, "032x")
            span_id = format(span.get_span_context().span_id, "016x")
            request_id = baggage.get_baggage("request.id")

            span.set_attribute("request.id", request_id)
            attributes = {
                "name": span_name,
                "request.id": request_id,
                "trace.id": trace_id,
                "step_id": span_id,
                "parent_id": baggage.get_baggage("parent_id"),
                "timestamp": int(datetime.now().timestamp() * 1_000_000),
                **self.get_attributes(),
            }

            _token = attach(baggage.set_baggage("parent_id", span_id))

            output = None
            try:
                if self.event_source == "task":
                    self.callback_handler.on_task_start({**attributes, "input_parameters": json.dumps(args)})
                elif self.event_source == "workflow":
                    self.callback_handler.on_workflow_start({**attributes, "input_parameters": json.dumps(args)})

                logger.info("Starting operation", operation=span_name)
                output = self.__wrapped__(*args, **kwargs)
                # _log_output = self._prepare_log_output(output)
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
                span.set_attribute("output", _output)
                end_time = time.perf_counter()
                ts_diff = end_time - start_time
                span.set_attribute("duration", ts_diff)
                detach(_token)
                if self.event_source == "task":
                    self.callback_handler.on_task_end({**attributes, "output": json.dumps(_output)})
                elif self.event_source == "workflow":
                    self.callback_handler.on_workflow_end({**attributes, "output": json.dumps(_output)})
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
            request_id = baggage.get_baggage("request.id")
            span_id = format(span.get_span_context().span_id, "016x")
            trace_id = format(span.get_span_context().trace_id, "032x")
            span.set_attribute("request_id", request_id)

            attributes = {
                "name": span_name,
                "request.id": request_id,
                "trace.id": trace_id,
                "step_id": span_id,
                "parent_id": baggage.get_baggage("parent_id"),
                "timestamp": int(datetime.now().timestamp() * 1_000_000),
                **self.get_attributes(),
            }

            _token = attach(baggage.set_baggage("parent_id", span_id))

            try:
                if self.event_source == "task":
                    self.callback_handler.on_task_start({**attributes, "input_parameters": json.dumps(args)})
                elif self.event_source == "workflow":
                    self.callback_handler.on_workflow_start({**attributes, "input_parameters": json.dumps(args)})
                logger.info(f"Starting operation - {span_name}")
                output = await self.__wrapped__(*args, **kwargs)
                logger.info(f"Operation completed successfully - {span_name}")
                if self.event_source == "task":
                    self.callback_handler.on_task_end({**attributes, "output": json.dumps(output)})
                elif self.event_source == "workflow":
                    self.callback_handler.on_workflow_end({**attributes, "output": json.dumps(output)})
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                logger.error(f"Operation failed - {span_name}", exc_info=True, error=str(e))
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise e
            finally:
                _output = self._prepare_log_output(output)
                span.set_attribute("output", _output)
                end_time = time.perf_counter()
                ts_diff = end_time - start_time
                span.set_attribute("duration", ts_diff)
                detach(_token)
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
    def instrument(project_dir: str, callback_handler: CallbackHandler):
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
            _task.config.func = InstrumentationWrapper(_task.config.func, callback_handler, "task")
            task_registry[task_name] = _task
        TaskConfig._registry = task_registry

        workflow_registry = WorkflowConfig._registry.copy()
        for workflow_name in WorkflowConfig._registry.keys():
            _workflow = WorkflowConfig._registry[workflow_name]
            _workflow.config.func = InstrumentationWrapper(_workflow.config.func, callback_handler, "workflow")
            workflow_registry[workflow_name] = _workflow
        WorkflowConfig._registry = workflow_registry

        logger.info(f"Found workflows - {WorkflowConfig.get_all()}")
