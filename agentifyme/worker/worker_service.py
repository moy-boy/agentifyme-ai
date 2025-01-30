import asyncio
import queue
import random
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import grpc
import orjson
from google.protobuf import struct_pb2
from grpc.aio import StreamStreamCall
from loguru import logger
from opentelemetry import baggage, trace
from opentelemetry.context import attach, detach
from opentelemetry.propagate import inject
from opentelemetry.trace import StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel

import agentifyme.worker.pb.api.v1.gateway_pb2 as pb
import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme import __version__
from agentifyme.components.workflow import WorkflowConfig
from agentifyme.errors import AgentifyMeError, ErrorCategory, ErrorSeverity
from agentifyme.utilities.grpc import (
    convert_for_protobuf,
    get_message_id,
    get_timestamp,
)
from agentifyme.worker.callback import CallbackHandler
from agentifyme.worker.helpers import convert_workflow_to_pb, struct_to_dict

# Import generated protobuf code (assuming pb directory structure matches Go)
from agentifyme.worker.pb.api.v1 import common_pb2
from agentifyme.worker.workflows import (
    WorkflowCommandHandler,
    WorkflowHandler,
    WorkflowJob,
)


async def exponential_backoff(attempt: int, max_delay: int = 32) -> None:
    """Exponential backoff with jitter"""
    delay = min(3**attempt, max_delay)
    jitter = random.uniform(0, 0.1) * delay
    total_delay = delay + jitter
    logger.info(f"Reconnection attempt {attempt + 1}, waiting {total_delay:.1f} seconds")
    await asyncio.sleep(total_delay)


tracer = trace.get_tracer(__name__)


class WorkerService:
    """Worker service for processing jobs."""

    MAX_RECONNECT_ATTEMPTS = 5  # Maximum number of reconnection attempts
    MAX_BACKOFF_DELAY = 32  # Maximum delay between attempts in seconds

    def __init__(
        self,
        stub: pb_grpc.GatewayServiceStub,
        callback_handler: CallbackHandler,
        api_gateway_url: str,
        project_id: str,
        deployment_id: str,
        worker_id: str,
        max_workers: int = 50,
        heartbeat_interval: int = 30,
    ):
        # configuration
        self.api_gateway_url = api_gateway_url
        self.project_id = project_id
        self.deployment_id = deployment_id
        self.worker_id = worker_id

        self.jobs_queue = asyncio.Queue()
        self.events_queue = asyncio.Queue()
        self.callback_event_queue = asyncio.Queue()
        self._event_loop = asyncio.get_event_loop()
        self.shutdown_event = asyncio.Event()
        self.active_jobs: dict[str, asyncio.Task] = {}
        self.job_semaphore = asyncio.Semaphore(max_workers)

        # workflow handlers.
        self._workflow_handlers: dict[str, WorkflowHandler] = {}
        self.workflow_semaphore = asyncio.Semaphore(max_workers)

        # tasks
        self.process_jobs_task: asyncio.Task | None = None
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._heartbeat_task: asyncio.Task | None = None
        self.health_status_task: asyncio.Task | None = None

        # state
        self._stub: pb_grpc.GatewayServiceStub | None = None
        self.worker_type = "python-worker"
        self.connected = False
        self.connection_event = asyncio.Event()

        self.running = True
        self._stream: StreamStreamCall | None = None
        self._workflow_command_handler = WorkflowCommandHandler(self._stream, max_workers)

        self._heartbeat_interval = heartbeat_interval
        self._stub = stub
        self.retry_attempt = 0

        # trace
        self._propagator = TraceContextTextMapPropagator()

        # health
        self.health_file = Path(f"/tmp/health/worker_{self.worker_id}.txt")
        self._last_health_state = None

        # callback handler
        self.callback_handler = callback_handler
        self.callback_handler.register_default(self.stream_events)

    async def start_service(self) -> bool:
        """Start the worker service."""
        # initialize workflow handlers
        workflow_handlers = self.initialize_workflow_handlers()
        workflow_names = list(workflow_handlers.keys())
        self._workflow_names = workflow_names
        self._workflow_handlers = workflow_handlers
        tasks = []

        try:
            # clean up health state at start
            self.health_file.unlink(missing_ok=True)
            self._last_health_state = False

            # start tasks
            self.health_status_task = asyncio.create_task(self._update_health_status())
            self.process_jobs_task = asyncio.create_task(self.process_jobs())
            self.subscribe_to_event_stream_task = asyncio.create_task(self.subscribe_to_event_stream())
            self.send_events_task = asyncio.create_task(self._send_events())
            self.process_callbacks_task = asyncio.create_task(self._process_callback_events())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            tasks = [
                self.process_jobs_task,
                self.subscribe_to_event_stream_task,
                self.send_events_task,
                self.heartbeat_task,
                self.health_status_task,
                self.process_callbacks_task,
            ]
            await asyncio.gather(*tasks)

            logger.info("Worker service started successfully")
            return True

        except Exception as e:
            # Handle any other unexpected errors
            for task in tasks:
                if task:
                    task.cancel()
            logger.error(f"Unexpected error during worker registration: {e!s}")
            return False

    async def subscribe_to_event_stream(self):
        while not self.shutdown_event.is_set():
            try:
                if self.retry_attempt >= self.MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"Failed to reconnect after {self.retry_attempt} attempts")
                    self.shutdown_event.set()
                    break

                logger.info(f"Subscribing to event stream with worker:{self.worker_id}")
                self._stream = self._stub.WorkerStream()

                msg = pb.InboundWorkerMessage(
                    msg_id=get_message_id(),
                    worker_id=self.worker_id,
                    deployment_id=self.deployment_id,
                    type=pb.INBOUND_WORKER_MESSAGE_TYPE_REGISTRATION,
                    timestamp=get_timestamp(),
                    registration=pb.WorkerRegistration(version=__version__, capabilities={}),
                )
                await self._stream.write(msg)

                async for msg in self._stream:
                    if self.shutdown_event.is_set():
                        break

                    if msg.HasField("ack") and msg.ack.success:
                        self.connected = True
                        self.connection_event.set()
                        await self.sync_workflows()
                        logger.info("🚀 Worker connected to API gateway. Listening for jobs...")
                        self.retry_attempt = 0

                    if msg.HasField("workflow_request"):
                        await self._handle_workflow_request(msg)

                    if msg.HasField("health_check"):
                        await self._handle_health_check(msg)

            except grpc.RpcError as e:
                self.connected = False
                logger.error(f"Stream error on attempt {self.retry_attempt + 1}/{self.MAX_RECONNECT_ATTEMPTS}: {e}")

            except Exception as e:
                self.connected = False
                logger.error(f"Unexpected error: {e}")

            finally:
                if not self.connected or self._stream is None:
                    await exponential_backoff(self.retry_attempt, self.MAX_BACKOFF_DELAY)
                    self.retry_attempt += 1
                    continue

    async def stop_service(self):
        self.shutdown_event.set()

        logger.info("Stopping worker service")

        # Cancel all running workflows
        for task in self.active_jobs.values():
            task.cancel()

        if self.active_jobs:
            await asyncio.gather(*self.active_jobs.values(), return_exceptions=True)

        if self.health_status_task:
            self.health_status_task.cancel()
            try:
                await self.health_status_task
            except asyncio.CancelledError:
                pass
            self.health_status_task = None
            self.health_file.unlink(missing_ok=True)

        await self._stop_heartbeat()

    async def sync_workflows(self) -> None:
        # Prepare workflow configs
        _workflows = [convert_workflow_to_pb(WorkflowConfig.get(name).config) for name in WorkflowConfig.get_all()]

        # Sync workflows
        sync_msg = pb.SyncWorkflowsRequest(
            worker_id=self.worker_id,
            deployment_id=self.deployment_id,
            workflows=_workflows,
        )
        response = await self._stub.SyncWorkflows(sync_msg)
        logger.info(f"Synchronized workflows: {str(response).strip()}")

    async def _receive_commands(self) -> None:
        """Receive and process commands from gRPC stream"""
        try:
            logger.info("Starting receive_commands")
            if self._stream is None:
                logger.error("Stream is not initialized")
                return

            async for msg in self._stream:
                if self.shutdown_event.is_set():
                    break

                logger.info(f"Received worker message: {msg.request_id}")
                # if isinstance(msg, pb.OutboundWorkerMessage):
                #     await self._handle_worker_message(msg)

        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC stream error in receive_commands: {e}")
            await self._handle_stream_error(e)
        except Exception as e:
            logger.exception(f"Unexpected error in receive_commands: {e}")
            raise

    async def _handle_health_check(self, msg: pb.OutboundWorkerMessage) -> None:
        """Handle incoming worker messages"""
        try:
            import psutil

            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage("/").percent
        except ImportError:
            logger.error("Error getting health check metrics: psutil not installed")
            cpu_usage = 0
            memory_usage = 0
            disk_usage = 0

        if self.connected:
            _msg = pb.InboundWorkerMessage(
                msg_id=get_message_id(),
                worker_id=self.worker_id,
                deployment_id=self.deployment_id,
                type=pb.INBOUND_WORKER_MESSAGE_TYPE_WORKER_STATUS,
                worker_status=pb.WorkerStatus(
                    state=pb.WORKER_STATE_READY,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    active_tasks=len(self.active_jobs),
                ),
            )
            await self._stream.write(_msg)

    async def _handle_workflow_request(self, msg: pb.OutboundWorkerMessage) -> None:
        """Handle workflow requests"""
        try:
            request = msg.workflow_request
            run_id = request.run_id
            workflow_name = request.workflow_name
            input_parameters = struct_to_dict(request.struct_input)

            # Extract tracing metadata
            carrier: dict[str, str] = getattr(msg, "metadata", {})
            carrier["run.id"] = run_id
            context = self._propagator.extract(carrier)

            # Set up baggage for request tracing
            token = attach(baggage.set_baggage("run.id", run_id))

            # Start tracing span
            with tracer.start_as_current_span(name="workflow.execute", context=context) as span:
                workflow_job = WorkflowJob(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    input_parameters=input_parameters,
                    metadata=carrier,
                )

                span.add_event(
                    "job_queued",
                    attributes={"run.id": run_id, "input_parameters": input_parameters},
                )

                await self.jobs_queue.put(workflow_job)
                logger.debug(f"Queued workflow job: {request.run_id}")

            detach(token)

        except Exception as e:
            logger.error(f"Error handling workflow request: {e}")

    # async def _handle_run_command(self, msg: pb.OutboundWorkerMessage, command: pb.WorkflowCommand) -> None:
    #     """Handle run workflow commands"""
    #     carrier: dict[str, str] = getattr(msg, "metadata", {})
    #     carrier["request_id"] = msg.request_id
    #     context = self._propagator.extract(carrier)

    #     token = attach(baggage.set_baggage("request.id", msg.request_id))
    #     with tracer.start_as_current_span(name="workflow.execute", context=context) as span:
    #         workflow_job = WorkflowJob(
    #             run_id=msg.request_id,
    #             workflow_name=command.run_workflow.workflow_name,
    #             input_parameters=struct_to_dict(command.run_workflow.parameters),
    #             metadata=carrier,
    #         )

    #         span.add_event("job_queued", attributes={"request_id": msg.request_id, "input_parameters": orjson.dumps(workflow_job.input_parameters)})

    #         await self.jobs_queue.put(workflow_job)
    #         logger.debug(f"Queued workflow job: {msg.request_id}")

    #     detach(token)

    async def _handle_workflow_command(self, msg: pb.OutboundWorkerMessage, command: pb.ControlCommand) -> None:
        """Handle workflow commands"""
        try:
            if command.type == pb.WORKFLOW_COMMAND_TYPE_RUN:
                await self._handle_run_command(msg, command)
            elif command.type == pb.WORKFLOW_COMMAND_TYPE_LIST:
                await self._handle_list_command(msg)
        except Exception as e:
            logger.error(f"Error handling workflow command: {e}")

    async def _handle_list_command(self, msg: pb.OutboundWorkerMessage) -> None:
        """Handle list workflows command"""
        response = await self._workflow_command_handler.list_workflows()
        reply = pb.InboundWorkerMessage(
            request_id=msg.request_id,
            worker_id=self.worker_id,
            deployment_id=self.deployment_id,
            type=pb.INBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS,
            list_workflows=response,
        )
        await self._stream.write(reply)

    async def _handle_stream_error(self, e: grpc.aio.AioRpcError) -> None:
        """Handle stream errors"""
        if e.code() == grpc.StatusCode.INTERNAL and "RST_STREAM" in str(e.details()):
            logger.warning(
                "Received RST_STREAM error, initiating graceful reconnect",
                extra={"error_details": e.details()},
            )
            self.connected = False
            return

        logger.error(f"gRPC stream error in receive_commands: {e}")
        raise

    def get_event_type(self, event_type: str) -> pb.RuntimeEventType:
        match event_type:
            case "workflow":
                return pb.RuntimeEventType.RUNTIME_EVENT_TYPE_WORKFLOW
            case "task":
                return pb.RuntimeEventType.RUNTIME_EVENT_TYPE_TASK
            case "llm":
                return pb.RuntimeEventType.RUNTIME_EVENT_TYPE_LLM
            case _:
                return pb.RuntimeEventType.RUNTIME_EVENT_TYPE_UNSPECIFIED

    def get_event_stage(self, event_stage: str) -> pb.RuntimeEventStage:
        match event_stage:
            case "initiated":
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_INITIATED
            case "finished":
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_FINISHED
            case "started":
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_STARTED
            case "completed":
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_COMPLETED
            case "cancelled":
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_CANCELLED
            case "timeout":
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_TIMEOUT
            case _:
                return pb.RuntimeEventStage.RUNTIME_EVENT_STAGE_UNSPECIFIED

    def _get_error(self, event: dict) -> common_pb2.AgentifyMeError | None:
        error = event.get("error")
        if error and isinstance(error, dict):
            return common_pb2.AgentifyMeError(
                message=error.get("message"),
                error_code=error.get("error_code"),
                category=error.get("category"),
                severity=error.get("severity"),
                traceback=error.get("traceback"),
                error_type=error.get("error_type"),
            )

    async def _send_events(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                if not self.connected or self._stream is None or self.events_queue.empty():
                    await asyncio.sleep(1)
                    continue

                event = await self.events_queue.get()
                try:
                    if isinstance(event, dict):
                        metadata = {}
                        metadata["project.id"] = self.project_id
                        metadata["deployment.id"] = self.deployment_id
                        metadata["worker.id"] = self.worker_id

                        event_stage = event.get("event_stage")

                        runtime_event = pb.RuntimeEvent(
                            event_type=self.get_event_type(event.get("event_type")),
                            event_stage=self.get_event_stage(event_stage),
                            event_name=event.get("event_name"),
                            timestamp=event.get("timestamp"),
                            event_id=event.get("step_id"),
                            parent_event_id=event.get("parent_id"),
                            run_id=event.get("run_id", "UNKNOWN"),
                            request_id=event.get("request.id", "UNKNOWN"),
                            idempotency_key=event.get("idempotency_key", "UNKNOWN"),
                            status=pb.RuntimeEventStatus.RUNTIME_EVENT_STATUS_SUCCESS,
                            retry_attempt=event.get("retry_attempt", 0),
                            metadata=metadata,
                            error=self._get_error(event),
                        )

                        if "input" in event:
                            input_data = event.get("input")
                            if isinstance(input_data, dict) or isinstance(input_data, BaseModel):
                                struct = struct_pb2.Struct()
                                struct.update(convert_for_protobuf(input_data))
                                runtime_event.input_data_format = pb.DATA_FORMAT_STRUCT
                                runtime_event.struct_input = struct
                            elif isinstance(input_data, bytes):
                                runtime_event.input_data_format = pb.DATA_FORMAT_BINARY
                                runtime_event.binary_input = input_data
                            elif isinstance(input_data, str):
                                runtime_event.input_data_format = pb.DATA_FORMAT_STRING
                                runtime_event.string_input = input_data
                            else:
                                logger.error(f"Received unexpected input type: {type(input_data)}")

                        if "output" in event:
                            output_data = event.get("output")
                            if isinstance(output_data, dict) or isinstance(output_data, BaseModel):
                                struct = struct_pb2.Struct()
                                struct.update(convert_for_protobuf(output_data))
                                runtime_event.output_data_format = pb.DATA_FORMAT_STRUCT
                                runtime_event.struct_output = struct
                            elif isinstance(output_data, bytes):
                                runtime_event.output_data_format = pb.DATA_FORMAT_BINARY
                                runtime_event.binary_output = output_data
                            elif isinstance(output_data, str):
                                runtime_event.output_data_format = pb.DATA_FORMAT_STRING
                                runtime_event.string_output = output_data
                            else:
                                logger.error(f"Received unexpected output type: {type(output_data)}")

                        msg = pb.InboundWorkerMessage(
                            msg_id=get_message_id(),
                            worker_id=self.worker_id,
                            deployment_id=self.deployment_id,
                            type=pb.INBOUND_WORKER_MESSAGE_TYPE_RUNTIME_EVENT,
                            event=runtime_event,
                            metadata=metadata,
                        )

                        await self._stream.write(msg)

                    else:
                        logger.debug(f"Received unexpected event type: {type(event)}")

                except grpc.aio.AioRpcError as e:
                    logger.error(f"Stream error in send_events: {e}")
                    self.connected = False  # Mark as disconnected on error
                    # Put the event back in the queue
                    await self.events_queue.put(event)
                    continue

                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"Error processing event: {e}")
                    continue

            except queue.Empty:
                pass

    async def process_jobs(self) -> None:
        """Process jobs from the queue"""
        while not self.shutdown_event.is_set():
            logger.info("Processing jobs from queue")
            try:
                job = await self.jobs_queue.get()
                asyncio.create_task(self._handle_job(job))
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)

    async def _handle_job(self, job: WorkflowJob):
        """Handle a single job"""
        async with self._workflow_context(job.run_id):
            try:
                carrier = job.metadata
                inject(carrier)
                context = self._propagator.extract(carrier)
                attributes = {"request.id": job.run_id}

                context = baggage.set_baggage("request.id", job.run_id, context=context)
                context = baggage.set_baggage("workflow.name", job.workflow_name, context=context)
                context = baggage.set_baggage("parent.id", "", context=context)
                token = attach(context=context)

                with tracer.start_as_current_span(name="handle.job", context=context, attributes=attributes) as span:
                    span_context = span.get_span_context()
                    trace_id = format(span_context.trace_id, "032x")
                    span_id = format(span.get_span_context().span_id, "016x")

                    attributes = {
                        "name": job.workflow_name,
                        "request.id": job.run_id,
                        "trace.id": trace_id,
                        "parent_id": "",
                        "step_id": span_id,
                        "timestamp": int(datetime.now().timestamp() * 1_000_000),
                    }

                    _token = attach(baggage.set_baggage("parent_id", span_id))

                    workflow_task = asyncio.current_task()
                    self.active_jobs[job.run_id] = workflow_task
                    span.add_event("job_started", attributes={"request.id": job.run_id})

                    logger.info(f"Workflow {job.run_id} started")

                    while not self.shutdown_event.is_set():
                        error = None
                        try:
                            self.callback_handler.fire_event(
                                "workflow.execution",
                                "initiated",
                                {**attributes, "input": job.input_parameters},
                            )
                            # Execute workflow step
                            _workflow_handler = self._workflow_handlers.get(job.workflow_name)
                            if _workflow_handler is None:
                                raise Exception(f"Workflow handler not found for {job.workflow_name}")

                            logger.info(f"Workflow {job.run_id} executing")
                            job = await _workflow_handler(job)

                            logger.info(f"SUCCESS ==> Workflow {job.run_id} result: {job.output}, job.success: {job.success}")

                            span.add_event(
                                "job_completed",
                                attributes={
                                    "request.id": job.run_id,
                                    "output": orjson.dumps(job.output),
                                    "success": job.success,
                                },
                            )

                            if job.success:
                                span.set_status(StatusCode.OK)
                            else:
                                span.set_status(StatusCode.ERROR, job.error)
                                error = job.error

                            # Send event
                            # await self.events_queue.put(job)

                            # If the job is completed, break out of the loop.
                            # TODO: Handle errors and retry scenario.
                            if job.completed:
                                break

                        except AgentifyMeError as e:
                            error = e
                            raise
                        except Exception as e:
                            error = AgentifyMeError(
                                message=str(e),
                                category=ErrorCategory.EXECUTION,
                                severity=ErrorSeverity.ERROR,
                                error_type=type(e).__name__,
                            )
                            raise
                        finally:
                            if error:
                                self.callback_handler.fire_event(
                                    "workflow.execution",
                                    "finished",
                                    {
                                        **attributes,
                                        "error": error.as_dict,
                                        "input": job.input_parameters,
                                    },
                                )
                            else:
                                self.callback_handler.fire_event(
                                    "workflow.execution",
                                    "finished",
                                    {
                                        **attributes,
                                        "output": job.output,
                                        "input": job.input_parameters,
                                    },
                                )
                detach(token)

            except asyncio.CancelledError:
                logger.info(f"Workflow {job.run_id} cancelled")
                raise
            except Exception as e:
                logger.error(f"Workflow execution error: {e}, {type(e)}")
                await self.events_queue.put({"workflow_id": job.run_id, "status": "error", "error": str(e)})

    @asynccontextmanager
    async def _workflow_context(self, run_id: str):
        """Context manager for workflow execution"""
        async with self.workflow_semaphore:
            try:
                yield
            finally:
                self.active_jobs.pop(run_id, None)

    async def _heartbeat_loop(self) -> None:
        """Continuously send heartbeats at the specified interval."""
        try:
            while not self.shutdown_event.is_set():
                await asyncio.sleep(self._heartbeat_interval)

                if not self.connected:
                    await asyncio.sleep(10.0)
                    continue

                try:
                    metrics = {
                        "num_active_jobs": len(self.active_jobs),
                        "num_jobs_in_queue": self.jobs_queue.qsize(),
                        "num_events_in_queue": self.events_queue.qsize(),
                    }
                    heartbeat_msg = pb.WorkerHeartbeatRequest(
                        worker_id=self.worker_id,
                        deployment_id=self.deployment_id,
                        status="active",
                        metrics=metrics,
                    )
                    _ = await self._stub.WorkerHeartbeat(heartbeat_msg)
                except grpc.RpcError as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                    # Instead of continuing in a loop, raise the error to trigger reconnection
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error in heartbeat: {e}")
                    raise

        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
            raise

    def _start_heartbeat(self, stream: StreamStreamCall) -> None:
        """Start the heartbeat task."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _stop_heartbeat(self) -> None:
        """Stop the heartbeat task."""
        if self._heartbeat_task is not None:
            await self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def cleanup_on_disconnect(self):
        """Cleanup resources on disconnect"""
        self.health_file.unlink(missing_ok=True)
        self._last_health_state = False

        self._stop_heartbeat()
        self.connected = False
        self.connection_event.clear()

        # Clear queues
        while not self.jobs_queue.empty():
            try:
                self.jobs_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        while not self.events_queue.empty():
            try:
                self.events_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Cancel active jobs
        for job_id, task in list(self.active_jobs.items()):
            logger.info(f"Cancelling job {job_id} due to disconnect")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error cancelling job {job_id}: {e}")

        self._active_tasks.clear()
        await asyncio.sleep(1)
        logger.info("Cleaned up disconnected resources")

    def initialize_workflow_handlers(self) -> dict[str, WorkflowHandler]:
        """Initialize workflow handlers"""
        logger.info(f"Found workflows - {WorkflowConfig.get_all()}")
        _workflow_handlers = {}
        for workflow_name in WorkflowConfig.get_all():
            _workflow = WorkflowConfig.get(workflow_name)
            _workflow_handler = WorkflowHandler(_workflow)
            _workflow_handlers[workflow_name] = _workflow_handler

        return _workflow_handlers

    async def _update_health_status(self):
        """Update health status file only when state changes"""
        while not self.shutdown_event.is_set():
            try:
                current_state = self.connected and not self.shutdown_event.is_set()

                # Only write/remove file if state has changed
                if current_state != self._last_health_state:
                    if current_state:
                        self.health_file.parent.mkdir(exist_ok=True)
                        self.health_file.touch()
                        self.health_file.write_text(str(int(datetime.now().timestamp() * 1_000_000)))
                        logger.info("Workflow service is healthy")
                    else:
                        self.health_file.unlink(missing_ok=True)
                        logger.info("Workflow service is unhealthy")
                    self._last_health_state = current_state

                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error updating health status: {e}")
                await asyncio.sleep(1)

    async def stream_events(self, data: dict):
        await self.events_queue.put(data)

    async def _process_callback_events(self):
        """Process jobs from the queue"""
        while not self.shutdown_event.is_set():
            logger.info("Processing jobs from queue")
            try:
                event_data = await self.callback_event_queue.get()
                asyncio.create_task(self._process_callback_event(event_data))
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)

    async def _process_callback_event(self, data: Any):
        # Create base event data
        event_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp() * 1_000_000)
        data["timestamp"] = timestamp

        # Clean data to ensure JSON serializable
        _data = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, list, dict, tuple, set))}
        json_data = orjson.dumps(_data).decode("utf-8")

        # Map event types to protobuf event types and data
        event_type_mapping = {
            "task_start": (pb.EVENT_TYPE_TASK_STARTED, "task_event", pb.TaskEventData),
            "task_end": (pb.EVENT_TYPE_TASK_COMPLETED, "task_event", pb.TaskEventData),
            "workflow_start": (
                pb.EVENT_TYPE_WORKFLOW_STARTED,
                "workflow_event",
                pb.WorkflowEventData,
            ),
            "workflow_end": (
                pb.EVENT_TYPE_WORKFLOW_COMPLETED,
                "workflow_event",
                pb.WorkflowEventData,
            ),
            "exec_start": (
                pb.EVENT_TYPE_EXECUTION_STARTED,
                "execution_event",
                pb.ExecutionEventData,
            ),
            "exec_end": (
                pb.EVENT_TYPE_EXECUTION_COMPLETED,
                "execution_event",
                pb.ExecutionEventData,
            ),
        }

        event_type = data["event_type"]
        if event_type not in event_type_mapping:
            logger.error(f"Unknown event type: {event_type}")
            return

        pb_event_type, event_field, event_class = event_type_mapping[event_type]

        # Build event data
        event_data = {"payload": json_data}
        if event_field == "execution_event":
            event_data["execution_id"] = str(uuid.uuid4())

        logger.info(f"Event data: {event_data}")

        # Create and send request
        request = pb.RuntimeExecutionEventRequest(
            event_id=event_id,
            timestamp=timestamp,
            event_type=pb_event_type,
            **{event_field: event_class(**event_data)},
        )

        await self._stub.RuntimeExecutionEvent(request)
