import asyncio
import signal
import sys
import traceback
import uuid
from typing import AsyncGenerator

import grpc
from loguru import logger

import agentifyme.worker.pb.api.v1.common_pb2 as common_pb2

# Import generated protobuf code (assuming pb directory structure matches Go)
import agentifyme.worker.pb.api.v1.worker_pb2 as worker_pb2
import agentifyme.worker.pb.api.v1.worker_pb2_grpc as worker_pb2_grpc
from agentifyme.worker.workflow_handler import WorkflowHandler
from agentifyme.workflows import WorkflowConfig


class WorkerService:
    def __init__(self, max_concurrent_jobs: int = 20):
        self.worker_id = str(uuid.uuid4())
        self.worker_type = "python-worker"
        self.capabilities = ["batch", "interactive"]
        self._workflow_handlers: dict[str, WorkflowHandler] = {}
        self.running = True
        self._stream = None
        self._job_semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self._current_jobs = 0
        self._active_tasks: dict[str, asyncio.Task] = {}

    def register_handler(self, name: str, handler: WorkflowHandler):
        self._workflow_handlers[name] = handler

    async def register(self) -> worker_pb2.WorkerStreamOutbound:
        registration = worker_pb2.WorkerRegistration(
            worker_type=self.worker_type, capabilities=self.capabilities
        )

        return worker_pb2.WorkerStreamOutbound(
            worker_id=self.worker_id,
            type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_REGISTER,
            registration=registration,
        )

    async def process_job(
        self, job: worker_pb2.JobAssignment
    ) -> AsyncGenerator[worker_pb2.WorkerStreamOutbound, None]:
        async with self._job_semaphore:
            try:
                self._current_jobs += 1
                logger.info(
                    f"Starting job {job.job_id}. Current concurrent jobs: {self._current_jobs}"
                )

                workflow_name = job.function.name
                if workflow_name not in self._workflow_handlers:
                    raise ValueError(
                        f"No handler registered for workflow: {workflow_name}"
                    )

                workflow_parameters = dict(job.function.parameters)

                logger.info(f"Processing job {job.job_id}")

                yield worker_pb2.WorkerStreamOutbound(
                    worker_id=self.worker_id,
                    type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_JOB_STATUS,
                    job=common_pb2.JobStatus(
                        job_id=job.job_id,
                        status=common_pb2.WORKER_JOB_STATUS_PROCESSING,
                        metadata=job.metadata,
                    ),
                )

                workflow_handler = self._workflow_handlers[workflow_name]
                result = await workflow_handler(workflow_parameters)

                yield worker_pb2.WorkerStreamOutbound(
                    worker_id=self.worker_id,
                    type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_JOB_RESULT,
                    result=common_pb2.JobResult(
                        job_id=job.job_id,
                        output=result,
                        metadata=job.metadata,
                    ),
                )

            except Exception as e:
                logger.error(f"Error processing job: {e}")
                yield worker_pb2.WorkerStreamOutbound(
                    worker_id=self.worker_id,
                    type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_JOB_ERROR,
                    error=common_pb2.JobError(
                        job_id=job.job_id, message=str(e), metadata=job.metadata
                    ),
                )
            finally:
                self._current_jobs -= 1
                logger.info(
                    f"Completed job {job.job_id}. Remaining concurrent jobs: {self._current_jobs}"
                )

    async def process_job_wrapper(self, job: worker_pb2.JobAssignment, stream) -> None:
        try:
            async with self._job_semaphore:
                logger.info(
                    f"Starting job {job.job_id}. Active tasks: {len(self._active_tasks)}"
                )

                # Send processing status
                await stream.write(
                    worker_pb2.WorkerStreamOutbound(
                        worker_id=self.worker_id,
                        type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_JOB_STATUS,
                        job=common_pb2.JobStatus(
                            job_id=job.job_id,
                            status=common_pb2.WORKER_JOB_STATUS_PROCESSING,
                            metadata=job.metadata,
                        ),
                    )
                )

                try:
                    workflow_name = job.function.name
                    if workflow_name not in self._workflow_handlers:
                        raise ValueError(
                            f"No handler registered for workflow: {workflow_name}"
                        )

                    workflow_parameters = dict(job.function.parameters)
                    workflow_handler = self._workflow_handlers[workflow_name]
                    result = await workflow_handler(workflow_parameters)

                    # Send success result
                    await stream.write(
                        worker_pb2.WorkerStreamOutbound(
                            worker_id=self.worker_id,
                            type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_JOB_RESULT,
                            result=common_pb2.JobResult(
                                job_id=job.job_id,
                                output=result,
                                metadata=job.metadata,
                            ),
                        )
                    )

                except Exception as e:
                    logger.error(f"Error processing job {job.job_id}: {e}")
                    # Send error result
                    await stream.write(
                        worker_pb2.WorkerStreamOutbound(
                            worker_id=self.worker_id,
                            type=worker_pb2.WORKER_SERVICE_OUTBOUND_TYPE_JOB_ERROR,
                            error=common_pb2.JobError(
                                job_id=job.job_id, message=str(e), metadata=job.metadata
                            ),
                        )
                    )

        finally:
            if job.job_id in self._active_tasks:
                del self._active_tasks[job.job_id]
            logger.info(
                f"Completed job {job.job_id}. Remaining tasks: {len(self._active_tasks)}"
            )

    # async def worker_stream(self, stub: worker_pb2_grpc.WorkerServiceStub) -> None:
    #     try:
    #         stream = stub.WorkerStream()
    #         self._stream = stream

    #         # Register worker with gateway
    #         reg_msg = await self.register()
    #         await stream.write(reg_msg)
    #         logger.info(f"Worker {self.worker_id} registered")

    #         while self.running:
    #             try:
    #                 message = await stream.read()
    #                 if message is None:  # Stream closed by server
    #                     logger.info("Stream closed by server")
    #                     break

    #                 if message.HasField("job"):
    #                     async for response in self.process_job(message.job):
    #                         if self.running:
    #                             await stream.write(response)
    #             except Exception as e:
    #                 logger.error(f"Stream error: {e}")
    #                 if not self.running:
    #                     break

    #     except Exception as e:
    #         logger.error(f"Stream error: {e}", exc_info=True)
    #         self.running = False
    #     finally:
    #         self._stream = None

    async def worker_stream(self, stub: worker_pb2_grpc.WorkerServiceStub) -> None:
        try:
            stream = stub.WorkerStream()
            self._stream = stream

            # Register worker with gateway
            reg_msg = await self.register()
            await stream.write(reg_msg)
            logger.info(f"Worker {self.worker_id} registered")

            while self.running:
                try:
                    message = await stream.read()
                    if message is None:  # Stream closed by server
                        logger.info("Stream closed by server")
                        break

                    if message.HasField("job"):
                        job = message.job
                        # Create new task for job processing
                        task = asyncio.create_task(
                            self.process_job_wrapper(job, stream)
                        )
                        self._active_tasks[job.job_id] = task

                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    if not self.running:
                        break

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            self.running = False
        finally:
            self._stream = None
            # Cancel any remaining tasks
            for task in self._active_tasks.values():
                task.cancel()


async def run_worker_service():
    # Handle immediate shutdown
    def signal_handler():
        logger.info("Shutting down worker immediately...")
        worker.running = False
        sys.exit(0)

    try:
        worker = WorkerService(max_concurrent_jobs=20)

        logger.info("Registering handlers")

        for workflow_name in WorkflowConfig.get_all():
            _workflow = WorkflowConfig.get(workflow_name)
            _workflow_handler = WorkflowHandler(_workflow)
            worker.register_handler(workflow_name, _workflow_handler)

        channel = grpc.aio.insecure_channel("localhost:60051")
        stub = worker_pb2_grpc.WorkerServiceStub(channel)

        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(sig, signal_handler)

        await worker.worker_stream(stub)

    except Exception as e:
        logger.error(f"Worker service error: {e}")
        logger.error(traceback.format_exc())
        traceback.print_exc()
    finally:
        await channel.close()
