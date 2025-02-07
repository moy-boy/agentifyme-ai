import asyncio
import os
from contextvars import ContextVar
from typing import Any, TypeVar, get_type_hints

import orjson
from grpc.aio import StreamStreamCall
from loguru import logger
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel

import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme.components.workflow import Workflow, WorkflowConfig
from agentifyme.errors import AgentifyMeError, ErrorContext
from agentifyme.worker.context import trace_id, workflow_name, workflow_run_id
from agentifyme.worker.helpers import build_args_from_signature

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
    error: AgentifyMeError | None
    output: dict | None
    metadata: dict[str, str]  # Metadata for the workflow execution trace.

    def __init__(self, run_id: str, workflow_name: str, input_parameters: dict, metadata: dict[str, str]):
        self.run_id = run_id
        self.workflow_name = workflow_name
        self.input_parameters = input_parameters
        self.metadata = metadata
        self.success = False
        self.error = None
        self.output = None


class WorkflowHandler:
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self._propagator = TraceContextTextMapPropagator()

    def _process_output(self, result: Any, return_type: type) -> dict[str, Any]:
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

    async def __call__(self, job: WorkflowJob) -> WorkflowJob:
        """Handle workflow execution with serialization/deserialization"""
        with tracer.start_as_current_span("workflow_execution") as span:
            try:
                # Get workflow configuration
                _workflow = WorkflowConfig.get(job.workflow_name)
                _workflow_config = _workflow.config

                # Build input arguments
                workflow_run_id.set(job.run_id)
                workflow_name.set(job.workflow_name)
                trace_id.set(format(span.get_span_context().trace_id, "032x"))

                func_args = build_args_from_signature(_workflow_config.func, job.input_parameters)

                # Log input
                span.add_event(
                    name="workflow.input",
                    attributes={"input": orjson.dumps(job.input_parameters).decode()},
                )

                logger.info(f"Executing workflow {job.run_id} with input: {func_args}")
                # Execute workflow
                if asyncio.iscoroutinefunction(_workflow_config.func):
                    result = await self.workflow.arun(**func_args)
                else:
                    result = self.workflow.run(**func_args)

                # Get return type and process output
                return_type = get_type_hints(_workflow_config.func).get("return")
                output_data = self._process_output(result, return_type)

                # Verify JSON serializable
                orjson.dumps(output_data)  # Will raise TypeError if not serializable

                job.output = output_data
                job.success = True

                # Record success
                span.set_status(Status(StatusCode.OK))
                span.add_event(name="workflow.complete", attributes={"output_size": len(str(output_data))})

            except AgentifyMeError as e:
                logger.error(f"AgentifyMeError: {e.message}")
                job.success = False
                job.error = e
                raise

            except Exception as e:
                job.output = None
                job.error = AgentifyMeError(
                    message=f"Workflow {job.run_id} execution error: {e}",
                    context=ErrorContext(component_type="workflow", component_id=job.workflow_name),
                    execution_state=job.input_parameters,
                )
                span.set_status(Status(StatusCode.ERROR, "Execution Error"))
                span.record_exception(e)
                span.add_event(name="workflow.execution_error", attributes={"error": str(e)})
                raise

            finally:
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

    # async def run_workflow(self, payload: pb.RunWorkflowCommand) -> dict | None:
    #     try:
    #         await self.stub.RuntimeExecutionEvent(
    #             pb.RuntimeExecutionEventRequest(
    #                 event_id=str(uuid.uuid4()),
    #                 timestamp=int(datetime.now().timestamp() * 1000),
    #                 event_type=pb.EVENT_TYPE_EXECUTION_QUEUED,
    #             )
    #         )
    #         async with self._job_semaphore:
    #             self._current_jobs += 1

    #             workflow_name = payload.workflow_name
    #             workflow_parameters = struct_to_dict(payload.parameters)

    #             logger.info(f"Running workflow {workflow_name} with parameters {workflow_parameters}")

    #             if workflow_name not in self.workflow_handlers:
    #                 raise ValueError(f"Workflow {workflow_name} not found")

    #             await self.stub.RuntimeExecutionEvent(
    #                 pb.RuntimeExecutionEventRequest(
    #                     event_id=str(uuid.uuid4()),
    #                     timestamp=int(datetime.now().timestamp() * 1000),
    #                     event_type=pb.EVENT_TYPE_EXECUTION_STARTED,
    #                 )
    #             )

    #             workflow_handler = self.workflow_handlers[workflow_name]
    #             result = await workflow_handler(workflow_parameters)

    #             await self.stub.RuntimeExecutionEvent(
    #                 pb.RuntimeExecutionEventRequest(
    #                     event_id=str(uuid.uuid4()),
    #                     timestamp=int(datetime.now().timestamp() * 1000),
    #                     event_type=pb.EVENT_TYPE_EXECUTION_COMPLETED,
    #                 )
    #             )

    #             return result
    #     except Exception as e:
    #         await self.stub.RuntimeExecutionEvent(
    #             pb.RuntimeExecutionEventRequest(
    #                 event_id=str(uuid.uuid4()),
    #                 timestamp=int(datetime.now().timestamp() * 1000),
    #                 event_type=pb.EVENT_TYPE_EXECUTION_FAILED,
    #             )
    #         )
    #         raise RuntimeError(f"Error running workflow: {str(e)}")
    #     finally:
    #         self._current_jobs -= 1
    #         logger.info(f"Finished job. Current concurrent jobs: {self._current_jobs}")

    # async def pause_workflow(self, payload: pb.PauseWorkflowCommand) -> str:
    #     pass

    # async def resume_workflow(self, payload: pb.ResumeWorkflowCommand) -> str:
    #     pass

    # async def cancel_workflow(self, payload: pb.CancelWorkflowCommand) -> str:
    #     pass

    # async def list_workflows(self) -> common_pb.ListWorkflowsResponse:
    #     pb_workflows: list[common_pb.WorkflowConfig] = []
    #     for workflow_name in WorkflowConfig.get_all():
    #         workflow = WorkflowConfig.get(workflow_name)
    #         workflow_config = workflow.config
    #         if isinstance(workflow_config, WorkflowConfig):
    #             _input_parameters = {}
    #             for (
    #                 input_parameter_name,
    #                 input_parameter,
    #             ) in workflow_config.input_parameters.items():
    #                 _input_parameters[input_parameter_name] = input_parameter.model_dump()

    #             _output_parameters = {}
    #             for idx, output_parameter in enumerate(workflow_config.output_parameters):
    #                 _output_parameters[f"output_{idx}"] = output_parameter.model_dump()

    #             pb_workflow = common_pb.WorkflowConfig(
    #                 name=workflow_config.name,
    #                 slug=workflow_config.slug,
    #                 description=workflow_config.description,
    #                 input_parameters=_input_parameters,
    #                 output_parameters=_output_parameters,
    #                 schedule=common_pb.Schedule(
    #                     cron_expression=workflow_config.normalize_schedule(workflow_config.schedule),
    #                 ),
    #             )
    #             pb_workflows.append(pb_workflow)

    #     return common_pb.ListWorkflowsResponse(workflows=pb_workflows)

    # async def __call__(self, command: pb.WorkflowCommand) -> dict | None:
    #     """Handle workflow command"""
    # match command.type:
    #     case pb.WORKFLOW_COMMAND_TYPE_RUN:
    #         return await self.run_workflow(command.run_workflow)
    #     case pb.WORKFLOW_COMMAND_TYPE_PAUSE:
    #         return await self.pause_workflow(command.pause_workflow)
    #     case pb.WORKFLOW_COMMAND_TYPE_RESUME:
    #         return await self.resume_workflow(command.resume_workflow)
    #     case pb.WORKFLOW_COMMAND_TYPE_CANCEL:
    #         return await self.cancel_workflow(command.cancel_workflow)
    #     case pb.WORKFLOW_COMMAND_TYPE_LIST:
    #         return await self.list_workflows()
    #     case _:
    #         raise ValueError(f"Unsupported workflow command type: {command.type}")
