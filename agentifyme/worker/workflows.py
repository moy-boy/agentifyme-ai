import asyncio
import os
import uuid
from datetime import datetime
from typing import TypeVar

import orjson
from grpc.aio import Channel, StreamStreamCall
from loguru import logger
from opentelemetry import trace
from opentelemetry.trace import SpanContext, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel, ValidationError

import agentifyme.worker.pb.api.v1.common_pb2 as common_pb
import agentifyme.worker.pb.api.v1.gateway_pb2 as pb
import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme.worker.helpers import convert_workflow_to_pb, struct_to_dict
from agentifyme.workflows import Workflow, WorkflowConfig

Input = TypeVar("Input")
Output = TypeVar("Output")

tracer = trace.get_tracer(__name__)


class WorkflowJob:
    """Workflow command"""

    run_id: str
    workflow_name: str
    input_parameters: dict
    completed: bool
    success: bool
    error: str | None
    output: dict | None

    def __init__(self, run_id: str, workflow_name: str, input_parameters: dict):
        self.run_id = run_id
        self.workflow_name = workflow_name
        self.input_parameters = input_parameters
        self.success = False
        self.error = None
        self.output = None


class WorkflowHandler:
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self._propagator = TraceContextTextMapPropagator()

    async def __call__(self, job: WorkflowJob) -> WorkflowJob:
        """Handle workflow execution with serialization/deserialization"""

        carrier: dict[str, str] = getattr(job, "metadata", {})
        context = self._propagator.extract(carrier)

        with tracer.start_as_current_span("workflow_execution", context=context) as span:
            try:
                # Deserialize input based on input type
                # if issubclass(self.input_type, BaseModel):
                #     parsed_input = self.input_type.model_validate(input_data)
                # elif issubclass(self.input_type, dict):
                #     parsed_input = input_data
                # else:
                #     raise ValueError(f"Unsupported input type: {type(self.input_type)}")

                span.add_event(
                    name="workflow.input",
                    attributes={"input": orjson.dumps(job.input_parameters).decode()},
                )

                parsed_input = job.input_parameters

                # Execute workflow
                result = await self.workflow.arun(**parsed_input)

                # Serialize output
                output_data = result
                if isinstance(result, BaseModel):
                    output_data = result.model_dump()
                # elif issubclass(self.output_type, dict):
                #     output_data = self.output_type(**result)
                # else:
                #     raise ValueError(f"Unsupported output type: {type(self.output_type)}")

                job.output = output_data
                job.success = True

                # Record the successful completion
                span.set_status(Status(StatusCode.OK))
                span.add_event(name="workflow.complete", attributes={"output_size": len(str(output_data))})

            except ValidationError as e:
                logger.error(f"Workflow {job.run_id} validation error: {e}")
                job.output = None
                job.error = str(e)
                span.set_status(Status(StatusCode.ERROR, "Validation Error"))
                span.record_exception(e)
                span.add_event(name="workflow.validation_error", attributes={"error": str(e)})

            except Exception as e:
                logger.error(f"Workflow {job.run_id} execution error: {e}")
                job.output = None
                job.error = str(e)
                span.set_status(Status(StatusCode.ERROR, "Execution Error"))
                span.record_exception(e)
                span.add_event(name="workflow.execution_error", attributes={"error": str(e)})

            finally:
                if hasattr(job, "metadata"):
                    self._propagator.inject(carrier=carrier)
                    job.metadata = carrier

            job.completed = True
            return job


class WorkflowCommandHandler:
    """Handle workflow commands"""

    workflow_handlers: dict[str, WorkflowHandler] = {}
    stub: pb_grpc.GatewayServiceStub

    def __init__(self, stream: StreamStreamCall, max_concurrent_jobs: int = 20):
        self.stream = stream
        self._current_jobs = 0
        self._max_concurrent_jobs = max_concurrent_jobs
        self._job_semaphore = asyncio.Semaphore(self._max_concurrent_jobs)
        for workflow_name in WorkflowConfig.get_all():
            _workflow = WorkflowConfig.get(workflow_name)
            _workflow_handler = WorkflowHandler(_workflow)
            self.workflow_handlers[workflow_name] = _workflow_handler

        self.deployment_id = os.getenv("AGENTIFYME_DEPLOYMENT_ID")
        self.worker_id = os.getenv("AGENTIFYME_WORKER_ID")

    def set_stub(self, stub: pb_grpc.GatewayServiceStub):
        self.stub = stub

    async def run_workflow(self, payload: pb.RunWorkflowCommand) -> dict | None:
        try:
            await self.stub.RuntimeExecutionEvent(
                pb.RuntimeExecutionEventRequest(
                    event_id=str(uuid.uuid4()),
                    timestamp=int(datetime.now().timestamp() * 1000),
                    event_type=pb.EVENT_TYPE_EXECUTION_QUEUED,
                )
            )
            async with self._job_semaphore:
                self._current_jobs += 1

                workflow_name = payload.workflow_name
                workflow_parameters = struct_to_dict(payload.parameters)

                logger.info(f"Running workflow {workflow_name} with parameters {workflow_parameters}")

                if workflow_name not in self.workflow_handlers:
                    raise ValueError(f"Workflow {workflow_name} not found")

                await self.stub.RuntimeExecutionEvent(
                    pb.RuntimeExecutionEventRequest(
                        event_id=str(uuid.uuid4()),
                        timestamp=int(datetime.now().timestamp() * 1000),
                        event_type=pb.EVENT_TYPE_EXECUTION_STARTED,
                    )
                )

                workflow_handler = self.workflow_handlers[workflow_name]
                result = await workflow_handler(workflow_parameters)

                await self.stub.RuntimeExecutionEvent(
                    pb.RuntimeExecutionEventRequest(
                        event_id=str(uuid.uuid4()),
                        timestamp=int(datetime.now().timestamp() * 1000),
                        event_type=pb.EVENT_TYPE_EXECUTION_COMPLETED,
                    )
                )

                return result
        except Exception as e:
            await self.stub.RuntimeExecutionEvent(
                pb.RuntimeExecutionEventRequest(
                    event_id=str(uuid.uuid4()),
                    timestamp=int(datetime.now().timestamp() * 1000),
                    event_type=pb.EVENT_TYPE_EXECUTION_FAILED,
                )
            )
            raise RuntimeError(f"Error running workflow: {str(e)}")
        finally:
            self._current_jobs -= 1
            logger.info(f"Finished job. Current concurrent jobs: {self._current_jobs}")

    async def pause_workflow(self, payload: pb.PauseWorkflowCommand) -> str:
        pass

    async def resume_workflow(self, payload: pb.ResumeWorkflowCommand) -> str:
        pass

    async def cancel_workflow(self, payload: pb.CancelWorkflowCommand) -> str:
        pass

    async def list_workflows(self) -> common_pb.ListWorkflowsResponse:
        pb_workflows: list[common_pb.WorkflowConfig] = []
        for workflow_name in WorkflowConfig.get_all():
            workflow = WorkflowConfig.get(workflow_name)
            workflow_config = workflow.config
            if isinstance(workflow_config, WorkflowConfig):
                _input_parameters = {}
                for (
                    input_parameter_name,
                    input_parameter,
                ) in workflow_config.input_parameters.items():
                    _input_parameters[input_parameter_name] = input_parameter.model_dump()

                _output_parameters = {}
                for idx, output_parameter in enumerate(workflow_config.output_parameters):
                    _output_parameters[f"output_{idx}"] = output_parameter.model_dump()

                pb_workflow = common_pb.WorkflowConfig(
                    name=workflow_config.name,
                    slug=workflow_config.slug,
                    description=workflow_config.description,
                    input_parameters=_input_parameters,
                    output_parameters=_output_parameters,
                    schedule=common_pb.Schedule(
                        cron_expression=workflow_config.normalize_schedule(workflow_config.schedule),
                    ),
                )
                pb_workflows.append(pb_workflow)

        return common_pb.ListWorkflowsResponse(workflows=pb_workflows)

    async def __call__(self, command: pb.WorkflowCommand) -> dict | None:
        """Handle workflow command"""
        match command.type:
            case pb.WORKFLOW_COMMAND_TYPE_RUN:
                return await self.run_workflow(command.run_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_PAUSE:
                return await self.pause_workflow(command.pause_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_RESUME:
                return await self.resume_workflow(command.resume_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_CANCEL:
                return await self.cancel_workflow(command.cancel_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_LIST:
                return await self.list_workflows()
            case _:
                raise ValueError(f"Unsupported workflow command type: {command.type}")
