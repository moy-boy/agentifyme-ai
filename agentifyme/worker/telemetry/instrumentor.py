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


def get_attributes():
    service_name = "agentifyme"

    attributes = {
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_INSTANCE_ID: socket.gethostname(),
        ResourceAttributes.SERVICE_VERSION: "0.0.35",
        ResourceAttributes.PROCESS_PID: os.getpid(),
    }

    if os.getenv("AGENTIFYME_ORGANIZATION_ID"):
        attributes["agentifyme.project.id"] = os.getenv("AGENTIFYME_ORGANIZATION_ID")

    if os.getenv("AGENTIFYME_PROJECT_ID"):
        attributes["agentifyme.project.id"] = os.getenv("AGENTIFYME_PROJECT_ID")

    if os.getenv("AGENTIFYME_REPLICA_ID"):
        attributes["agentifyme.replica.id"] = os.getenv("AGENTIFYME_REPLICA_ID")

    if os.getenv("AGENTIFYME_DEPLOYMENT_ID"):
        attributes["agentifyme.deployment.id"] = os.getenv("AGENTIFYME_DEPLOYMENT_ID")

    if os.getenv("AGENTIFYME_WORKER_ENDPOINT"):
        attributes["agentifyme.deployment.endpoint"] = os.getenv(
            "AGENTIFYME_WORKER_ENDPOINT"
        )

    if os.getenv("AGENTIFYME_ENV"):
        attributes["agentifyme.env"] = os.getenv("AGENTIFYME_ENV")

    return attributes


def add_context_attributes(logger, method_name, event_dict):
    attributes = get_attributes()
    for key, value in attributes.items():
        event_dict[key] = value
    return event_dict


def rename_event_to_message(logger, method_name, event_dict):
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


class InstrumentationWrapper(wrapt.ObjectProxy):
    tracer = trace.get_tracer("agentifyme-worker")

    # # Create a meter
    # meter = metrics.get_meter("agentifyme")

    # # Create some metrics
    # workflow_duration = meter.create_histogram(
    #     name="workflow_duration",
    #     description="Duration of workflow execution",
    #     unit="s",
    # )

    # task_duration = meter.create_histogram(
    #     name="task_duration",
    #     description="Duration of task execution",
    #     unit="s",
    # )

    # workflow_counter = meter.create_counter(
    #     name="workflows_executed",
    #     description="Number of workflows executed",
    # )

    # task_counter = meter.create_counter(
    #     name="tasks_executed",
    #     description="Number of tasks executed",
    # )

    # fn_call_counter = meter.create_counter(
    #     name="fn.total.count", description="Number of function calls"
    # )

    # fn_error_counter = meter.create_counter(
    #     name="fn.errors.count",
    #     description="Number of function call errors",
    # )

    def get_attributes(self):
        project_id = os.getenv("AGENTIFYME_PROJECT_ID", default="UNKNOWN")
        deployment_id = os.getenv("AGENTIFYME_DEPLOYMENT_ID", default="UNKNOWN")
        replica_id = os.getenv("AGENTIFYME_REPLICA_ID", default="UNKNOWN")
        endpoint = os.getenv("AGENTIFYME_ENDPOINT", default="UNKNOWN")
        return {
            SemanticAttributes.PROJECT_ID: project_id,
            SemanticAttributes.DEPLOYMENT_ID: deployment_id,
            SemanticAttributes.WORKER_REPLICA_ID: replica_id,
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
                logger.info("Operation completed successfully", result=_log_output)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                traceback.print_exc()
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
    def instrument():
        WorkflowConfig.reset_registry()
        TaskConfig.reset_registry()
        project_dir = os.getenv("AGENTIFYME_PROJECT_DIR", "/home/agnt5/app")
        working_directory = os.getcwd()

        if not os.path.exists(project_dir):
            logger.warning(
                f"Project directory not found. Defaulting to working directory: {working_directory}"
            )
            project_dir = working_directory

        # # if ./src exists, load modules from there
        if os.path.exists(os.path.join(project_dir, "src")):
            project_dir = os.path.join(project_dir, "src")

        logger.info(
            f"Loading workflows and tasks from project directory - {project_dir}"
        )
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
