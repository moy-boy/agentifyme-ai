import asyncio
import signal
import sys
import traceback

import grpc
from grpc.aio import StreamStreamCall
from loguru import logger

import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme.worker.worker_service import WorkerService


async def run(
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

    while worker.running:
        try:
            if retry_attempt > 0:
                if retry_attempt >= len(retry_delays):
                    logger.error(f"Failed to establish stable connection after {len(retry_delays)} attempts")
                    logger.error("Worker service shutting down")
                    sys.exit(1)

                delay = retry_delays[retry_attempt - 1]
                logger.info(f"Reconnection attempt {retry_attempt} of {len(retry_delays)}. Waiting {delay} seconds...")
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
            worker._workflow_command_handler.set_stub(stub)

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
                logger.warning(f"Gateway unavailable (attempt {retry_attempt}/{len(retry_delays)}, " f"{remaining_attempts} attempts remaining): {e.details()}")
            else:
                logger.error(f"gRPC error (attempt {retry_attempt}/{len(retry_delays)}, " f"{remaining_attempts} attempts remaining): {e.code()}: {e.details()}")

        except Exception as e:
            retry_attempt += 1
            remaining_attempts = len(retry_delays) - retry_attempt

            logger.error(f"Worker service error (attempt {retry_attempt}/{len(retry_delays)}, " f"{remaining_attempts} attempts remaining): {e}")
            logger.error(traceback.format_exc())

        finally:
            try:
                await channel.close()
            except Exception as e:
                logger.error(f"Error closing channel: {e}")

            # Reset retry count if we've been connected for a while
            if retry_attempt > 0 and worker.running:
                retry_attempt = 0  # Reset retry attempts to allow fresh reconnection attempts
