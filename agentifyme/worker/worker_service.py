import asyncio
import signal
import sys
import traceback

import grpc
from grpc.aio import StreamStreamCall
from loguru import logger

import agentifyme.worker.pb.api.v1.common_pb2 as common_pb

# Import generated protobuf code (assuming pb directory structure matches Go)
import agentifyme.worker.pb.api.v1.gateway_pb2 as pb
import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme.worker.workflows import WorkflowCommandHandler


class WorkerService:
    def __init__(
        self,
        deployment_id: str,
        worker_id: str,
        workflows: list[str],
        max_concurrent_jobs: int = 20,
        heartbeat_interval: int = 60,
    ):
        self.deployment_id = deployment_id
        self.worker_id = worker_id
        self.workflows = workflows
        self.worker_type = "python-worker"
        self.connected = False
        self.running = True
        self._stream: StreamStreamCall | None = None
        self._workflow_command_handler = WorkflowCommandHandler(
            self._stream, max_concurrent_jobs
        )
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._heartbeat_task: asyncio.Task | None = None
        self._heartbeat_interval = heartbeat_interval

    async def register_worker(self) -> pb.InboundWorkerMessage:
        registration = pb.WorkerRegistration(workflows=self.workflows)

        return pb.InboundWorkerMessage(
            worker_id=self.worker_id,
            deployment_id=self.deployment_id,
            type=pb.INBOUND_WORKER_MESSAGE_TYPE_REGISTER,
            registration=registration,
        )

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

    async def process_workflow_command(
        self, command: pb.WorkflowCommand, stream: StreamStreamCall
    ) -> None:
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
                            result = await self._workflow_command_handler(
                                message.workflow_command
                            )
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
                            response = (
                                await self._workflow_command_handler.list_workflows()
                            )
                            msg = pb.InboundWorkerMessage(
                                request_id=message.request_id,
                                worker_id=self.worker_id,
                                deployment_id=self.deployment_id,
                                type=pb.INBOUND_WORKER_MESSAGE_TYPE_LIST_WORKFLOWS,
                                list_workflows=response,
                            )
                            await stream.write(msg)

                        case _:
                            logger.error(
                                f"Received unexpected message type: {message.type}"
                            )

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


async def run_worker_service(
    deployment_id: str,
    worker_id: str,
    api_gateway_url: str,
    workflows: list[str],
):
    def signal_handler():
        logger.info("Shutting down worker immediately...")
        worker.running = False
        sys.exit(0)

    worker = WorkerService(deployment_id, worker_id, workflows, max_concurrent_jobs=20)
    retry_delays = [5, 10, 20, 45, 90]  # Specific retry delays in seconds
    retry_attempt = 0

    while worker.running:  # Continue as long as worker is running
        try:
            if retry_attempt > 0:
                if retry_attempt >= len(retry_delays):
                    logger.error(
                        f"Failed to establish stable connection after {len(retry_delays)} attempts"
                    )
                    logger.error("Worker service shutting down")
                    sys.exit(1)

                delay = retry_delays[retry_attempt - 1]
                logger.info(
                    f"Reconnection attempt {retry_attempt} of {len(retry_delays)}. Waiting {delay} seconds..."
                )
                await asyncio.sleep(delay)

            channel = grpc.aio.insecure_channel(
                api_gateway_url,
                options=[
                    ("grpc.keepalive_time_ms", 60000),
                    ("grpc.keepalive_timeout_ms", 20000),
                    ("grpc.keepalive_permit_without_calls", True),
                    ("grpc.enable_retries", 1),
                ],
            )
            stub = pb_grpc.GatewayServiceStub(channel)

            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_event_loop().add_signal_handler(sig, signal_handler)

            # Mark connection attempt
            if retry_attempt > 0:
                logger.info(f"Connection attempt {retry_attempt + 1} successful")

            await worker.worker_stream(stub)

            # If we get here, the stream ended normally
            if worker.running:
                logger.info("Stream ended, attempting to reconnect...")
                retry_attempt += 1
            else:
                break

        except grpc.aio.AioRpcError as e:
            retry_attempt += 1
            remaining_attempts = len(retry_delays) - retry_attempt

            if e.code() == grpc.StatusCode.UNAVAILABLE:
                logger.warning(
                    f"Gateway unavailable (attempt {retry_attempt}/{len(retry_delays)}, "
                    f"{remaining_attempts} attempts remaining): {e.details()}"
                )
            else:
                logger.error(
                    f"gRPC error (attempt {retry_attempt}/{len(retry_delays)}, "
                    f"{remaining_attempts} attempts remaining): {e.code()}: {e.details()}"
                )

        except Exception as e:
            retry_attempt += 1
            remaining_attempts = len(retry_delays) - retry_attempt

            logger.error(
                f"Worker service error (attempt {retry_attempt}/{len(retry_delays)}, "
                f"{remaining_attempts} attempts remaining): {e}"
            )
            logger.error(traceback.format_exc())

        finally:
            try:
                await channel.close()
            except Exception as e:
                logger.error(f"Error closing channel: {e}")

            # Reset retry count if we've been connected for a while
            if retry_attempt > 0 and worker.running:
                retry_attempt = (
                    0  # Reset retry attempts to allow fresh reconnection attempts
                )
