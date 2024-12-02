import asyncio
import queue
import traceback
from contextlib import asynccontextmanager

import grpc
from grpc.aio import StreamStreamCall
from loguru import logger
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

import agentifyme.worker.pb.api.v1.common_pb2 as common_pb

# Import generated protobuf code (assuming pb directory structure matches Go)
import agentifyme.worker.pb.api.v1.gateway_pb2 as pb
import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme.config import TaskConfig, WorkflowConfig
from agentifyme.worker.workflows import WorkflowCommandHandler, WorkflowHandler, WorkflowJob


async def exponential_backoff(attempt: int, max_delay: int = 32) -> None:
    delay = min(2**attempt, max_delay)
    logger.info(f"Reconnection attempt {attempt+1}, waiting {delay} seconds")
    await asyncio.sleep(delay)


tracer = trace.get_tracer(__name__)


class WorkerService:
    """
    Worker service for processing jobs.
    """

    MAX_RECONNECT_ATTEMPTS = 5  # Maximum number of reconnection attempts
    MAX_BACKOFF_DELAY = 32  # Maximum delay between attempts in seconds

    def __init__(
        self,
        stub: pb_grpc.GatewayServiceStub,
        api_gateway_url: str,
        project_id: str,
        deployment_id: str,
        worker_id: str,
        max_workers: int = 50,
        heartbeat_interval: int = 60,
    ):
        # configuration
        self.api_gateway_url = api_gateway_url
        self.project_id = project_id
        self.deployment_id = deployment_id
        self.worker_id = worker_id

        self.jobs_queue = asyncio.Queue()
        self.events_queue = asyncio.Queue()
        self.shutdown_event = asyncio.Event()
        self.active_jobs: dict[str, asyncio.Task] = {}
        self.job_semaphore = asyncio.Semaphore(max_workers)

        # workflow handlers.
        self._workflow_handlers: dict[str, WorkflowHandler] = {}
        self.workflow_semaphore = asyncio.Semaphore(max_workers)

        # state
        self._stub: pb_grpc.GatewayServiceStub | None = None
        self.worker_type = "python-worker"
        self.connected = False
        self.running = True
        self._stream: StreamStreamCall | None = None
        self._workflow_command_handler = WorkflowCommandHandler(self._stream, max_workers)
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._heartbeat_task: asyncio.Task | None = None
        self._heartbeat_interval = heartbeat_interval
        self._stub = stub

        # trace
        self._propagator = TraceContextTextMapPropagator()

    async def start_service(self):
        """Start the worker service."""  # initialize workflow handlers
        workflow_handlers = self.initialize_workflow_handlers()
        workflow_names = list(workflow_handlers.keys())
        self._workflow_handlers = workflow_handlers

        try:
            self._stream = self._stub.WorkerStream()

            # register worker
            msg = pb.InboundWorkerMessage(
                worker_id=self.worker_id,
                deployment_id=self.deployment_id,
                type=pb.INBOUND_WORKER_MESSAGE_TYPE_REGISTER,
                registration=pb.WorkerRegistration(workflows=workflow_names),
            )

            response = await self._stream.write(msg)
            logger.info(f"Registered worker: {response}")

        except grpc.RpcError as e:
            # Handle gRPC specific errors
            logger.error(f"Failed to register worker: {e.details()}")
            return False

        except Exception as e:
            # Handle any other unexpected errors
            traceback.print_exc()
            logger.error(f"Unexpected error during worker registration: {str(e)}")
            return False

    async def stop_service(self):
        self.shutdown_event.set()

        # Cancel all running workflows
        for task in self.active_jobs.values():
            task.cancel()

        if self.active_jobs:
            await asyncio.gather(*self.active_jobs.values(), return_exceptions=True)

    async def start_worker_stream(self) -> None:
        """Start the worker stream. This should be called after registering the worker. It handles the bidirectional stream with the API gateway.
        We listen to commands from the server, execute the commands and respond through events."""

        attempt = 0

        while not self.shutdown_event.is_set():
            try:
                if attempt >= self.MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"Failed to reconnect after {attempt} attempts")
                    self.shutdown_event.set()
                    break

                if self._stream is None:
                    await self.start_service()

                await asyncio.gather(
                    self._receive_commands(),
                    self._send_events(),
                    self._process_jobs(),
                    # self._heartbeat_loop(self._stream),
                )

                attempt = 0

            except grpc.RpcError as e:
                logger.error(f"Stream error on attempt {attempt+1}/{self.MAX_RECONNECT_ATTEMPTS}: {e}")
                if not self.shutdown_event.is_set():
                    self._stream = None
                    await self.cleanup_on_disconnect()
                    await exponential_backoff(attempt, self.MAX_BACKOFF_DELAY)
                    attempt += 1
                    continue

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if not self.shutdown_event.is_set():
                    self._stream = None
                    await self.cleanup_on_disconnect()
                    await exponential_backoff(attempt, self.MAX_BACKOFF_DELAY)
                    attempt += 1
                    continue

    async def _receive_commands(self) -> None:
        """Receive commands from gRPC stream"""
        try:
            async for stream_msg in self._stream:
                logger.info(f"Received stream message: {stream_msg}")
                if isinstance(stream_msg, pb.OutboundWorkerMessage):
                    # carrier: dict[str, str] = getattr(stream_msg, "metadata", {})
                    # context = self._propagator.extract(carrier)

                    # with tracer.start_as_current_span(
                    #     name="workflow.execute",
                    #     context=context,
                    # ) as span:
                    if stream_msg.HasField("workflow_command"):
                        workflow_command = stream_msg.workflow_command
                        match workflow_command.type:
                            case pb.WORKFLOW_COMMAND_TYPE_RUN:
                                _workflow_command = WorkflowJob(
                                    run_id=stream_msg.request_id,
                                    workflow_name=workflow_command.run_workflow.workflow_name,
                                    input_parameters=dict(workflow_command.run_workflow.parameters),
                                )

                                await self.jobs_queue.put(_workflow_command)
                            case pb.WORKFLOW_COMMAND_TYPE_LIST:
                                response = await self._workflow_command_handler.list_workflows()
                                logger.info(f"Listing workflows: {response}")
                                msg = pb.InboundWorkerMessage(
                                    request_id=stream_msg.request_id,
                                    worker_id=self.worker_id,
                                    deployment_id=self.deployment_id,
                                    type=pb.INBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS,
                                    list_workflows=response,
                                )
                                await self._stream.write(msg)

                    elif stream_msg.HasField("ack"):
                        if stream_msg.ack.status == "registered":
                            self.connected = True
                            logger.info("Registered worker")
                        else:
                            logger.error("Failed to register worker")
                            self.connected = False
                    elif stream_msg.HasField("workflow_status"):
                        pass

        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC stream error: {e}")
            traceback.print_exc()
            raise e

    async def _send_events(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                job = await self.events_queue.get()
                logger.info(f"Sending event: {job.run_id}, job.success: {job.success}, Job: {job}")

                if isinstance(job, WorkflowJob):
                    msg = pb.InboundWorkerMessage(
                        request_id=job.run_id,
                        worker_id=self.worker_id,
                        deployment_id=self.deployment_id,
                        type=pb.INBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_RESULT,
                        workflow_result=common_pb.WorkflowResult(request_id=job.run_id, data=job.output, error=job.error),
                    )

                    logger.info(f"Sending workflow result: {msg}")
                    await self._stream.write(msg)
                else:
                    logger.error(f"Received unexpected job type: {type(job)}")
            except queue.Empty:
                pass

    async def _process_jobs(self) -> None:
        """Process jobs from the queue"""
        while not self.shutdown_event.is_set():
            try:
                job = await self.jobs_queue.get()
                asyncio.create_task(self._handle_job(job))
            except Exception as e:
                self.logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)

    async def _handle_job(self, job: WorkflowJob):
        """Handle a single job"""
        async with self._workflow_context(job.run_id):
            try:
                workflow_task = asyncio.current_task()
                self.active_jobs[job.run_id] = workflow_task

                while not self.shutdown_event.is_set():
                    # Execute workflow step
                    _workflow_handler = self._workflow_handlers.get(job.workflow_name)
                    job = await _workflow_handler(job)

                    logger.info(f"Workflow {job.run_id} result: {job.output}, job.success: {job.success}")

                    # Send event
                    await self.events_queue.put(job)

                    # If the job is completed, break out of the loop.
                    # TODO: Handle errors and retry scenario.
                    if job.completed:
                        break

            except asyncio.CancelledError:
                self.logger.info(f"Workflow {job.run_id} cancelled")
                raise
            except Exception as e:
                self.logger.error(f"Workflow execution error: {e}")
                await self.event_queue.put({"workflow_id": job.run_id, "status": "error", "error": str(e)})

    @asynccontextmanager
    async def _workflow_context(self, run_id: str):
        """Context manager for workflow execution"""
        async with self.workflow_semaphore:
            try:
                yield
            finally:
                self.active_jobs.pop(run_id, None)

    async def _heartbeat_loop(self, stream: StreamStreamCall) -> None:
        """Continuously send heartbeats at the specified interval."""
        try:
            while self.running and self.connected:
                logger.debug(f"Sending heartbeat for worker {self.worker_id}")
                heartbeat = pb.WorkerHeartbeat(status="active")
                heartbeat_msg = pb.InboundWorkerMessage(
                    worker_id=self.worker_id,
                    type=pb.INBOUND_WORKER_MESSAGE_TYPE_HEARTBEAT,
                    heartbeat=heartbeat,
                )

                try:
                    await stream.write(heartbeat_msg)
                    logger.debug(f"Sent heartbeat for worker {self.worker_id}")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                    break

                await asyncio.sleep(self._heartbeat_interval)
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
            raise

    def _start_heartbeat(self, stream: StreamStreamCall) -> None:
        """Start the heartbeat task."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(stream))

    def _stop_heartbeat(self) -> None:
        """Stop the heartbeat task."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def cleanup_on_disconnect(self):
        """Cleanup resources on disconnect"""
        self._stop_heartbeat()
        self.connected = False

        for task in self._active_tasks.values():
            task.cancel()

        self._active_tasks.clear()
        await asyncio.sleep(1)
        logger.info("Cleaned up disconnected resources")

    async def process_workflow_command(self, command: pb.WorkflowCommand, stream: StreamStreamCall) -> None:
        try:
            async with self._job_semaphore:
                self._current_jobs += 1

                #             workflow_name = job.function.name
        #             if workflow_name not in self._workflow_handlers:
        #                 raise ValueError(
        #                     f"No handler registered for workflow: {workflow_name}"
        #                 )

        #             workflow_parameters = dict(job.function.parameters)

        #             logger.info(f"Processing job {job.job_id}")

        #             yield pb.WorkerStreamOutbound(
        #                 worker_id=self.worker_id,
        #                 type=pb.WORKER_SERVICE_OUTBOUND_TYPE_JOB_STATUS,
        #                 job=common_pb2.JobStatus(
        #                     job_id=job.job_id,
        #                     status=common_pb2.WORKER_JOB_STATUS_PROCESSING,
        #                     metadata=job.metadata,
        #                 ),
        #             )

        #             workflow_handler = self._workflow_handlers[workflow_name]
        #             result = await workflow_handler(workflow_parameters)

        except Exception as e:
            logger.error(f"Error processing workflow command: {e}")
        finally:
            self._current_jobs -= 1

    async def send_heartbeat(self, stream: StreamStreamCall) -> None:
        heartbeat = pb.WorkerHeartbeat(status="active")

        heartbeat_msg = pb.InboundWorkerMessage(
            worker_id=self.worker_id,
            type=pb.INBOUND_WORKER_MESSAGE_TYPE_HEARTBEAT,
            heartbeat=heartbeat,
        )

        await stream.write(heartbeat_msg)

    async def worker_stream(self, stub: pb_grpc.GatewayServiceStub) -> None:
        try:
            stream: StreamStreamCall = stub.WorkerStream()
            self._stream = stream

            # Register worker with gateway
            reg_msg: pb.InboundWorkerMessage = await self.register_worker()
            logger.info(f"Sending registration: {reg_msg}")
            await stream.write(reg_msg)
            logger.info(f"Worker {self.worker_id} registered")

            async for message in stream:
                if isinstance(message, pb.OutboundWorkerMessage):
                    match message.type:
                        case pb.OUTBOUND_WORKER_MESSAGE_TYPE_ACK:
                            if message.ack.status == "registered":
                                self.connected = True
                                logger.info("Registered worker")

                                # Start heartbeat
                                self._start_heartbeat(stream)
                            else:
                                logger.error("Failed to register worker")
                                self.connected = False
                                return

                        case pb.OUTBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_COMMAND:
                            result = await self._workflow_command_handler(message.workflow_command)
                            if result is not None:
                                msg = pb.InboundWorkerMessage(
                                    request_id=message.request_id,
                                    worker_id=self.worker_id,
                                    deployment_id=self.deployment_id,
                                    type=pb.INBOUND_WORKER_MESSAGE_TYPE_WORKFLOW_RESULT,
                                    workflow_result=common_pb.WorkflowResult(
                                        request_id=message.request_id,
                                        data=result,
                                    ),
                                )
                                await stream.write(msg)

                        case pb.OUTBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS:
                            response = await self._workflow_command_handler.list_workflows()
                            msg = pb.InboundWorkerMessage(
                                request_id=message.request_id,
                                worker_id=self.worker_id,
                                deployment_id=self.deployment_id,
                                type=pb.INBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS,
                                list_workflows=response,
                            )
                            await stream.write(msg)

                        case _:
                            logger.error(f"Received unexpected message type: {message.type}")

        except grpc.aio.AioRpcError as e:
            match e.code():
                case grpc.StatusCode.UNAVAILABLE:
                    logger.warning(f"Gateway unavailable: {e.details()}")
                    return
                case grpc.StatusCode.UNIMPLEMENTED:
                    logger.warning(f"Unsupported command: {e.details()}")
                    return
                case _:
                    logger.error(f"Stream error: {e.code()}: {e.details()}")
                    if not self.running:
                        return

            if not self.running:
                return

            # Log error but don't exit
            logger.error(traceback.format_exc())
            return  # Return to allow reconnection

        except Exception as e:
            traceback.print_exc()
            logger.error(f"Stream error: {e}", exc_info=True)
            self.running = True  # Keep running to allow reconnection
            return
        finally:
            # Stop heartbeat
            self._stop_heartbeat()

            self._stream = None
            # Cancel any remaining tasks
            for task in self._active_tasks.values():
                task.cancel()

    def initialize_workflow_handlers(self) -> dict[str, WorkflowHandler]:
        """Initialize workflow handlers"""
        _workflow_handlers = {}
        for workflow_name in WorkflowConfig.get_all():
            _workflow = WorkflowConfig.get(workflow_name)
            _workflow_handler = WorkflowHandler(_workflow)
            _workflow_handlers[workflow_name] = _workflow_handler

        return _workflow_handlers

    async def cleanup_on_disconnect(self):
        await asyncio.sleep(1)
        logger.info("Cleanup on disconnect")
