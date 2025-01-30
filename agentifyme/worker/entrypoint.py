import asyncio
import os
import sys
from pathlib import Path

import grpc
from importlib_metadata import PackageNotFoundError, version
from loguru import logger

import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme import __version__
from agentifyme.utilities.modules import (
    load_modules_from_directory,
)
from agentifyme.worker.auth_interceptor import APIKeyInterceptor
from agentifyme.worker.callback import CallbackHandler
from agentifyme.worker.telemetry import (
    auto_instrument,
    setup_telemetry,
)
from agentifyme.worker.worker_service import WorkerService


def main():
    exit_code = 1
    try:
        initialize_sentry()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        exit_code = loop.run_until_complete(run())
    except KeyboardInterrupt:
        logger.info("Worker service stopped by user")
        exit_code = 0
    except Exception as e:
        logger.error("Worker service error", exc_info=True, error=str(e))
        exit_code = 1
    finally:
        # Ensure logger is properly closed and flush outputs
        try:
            logger.remove()
            sys.stdout.flush()
            sys.stderr.flush()
            loop.close()
        except Exception as e:
            logger.error("Failed to close logger", exc_info=True, error=str(e))

    sys.exit(exit_code)


def initialize_sentry():
    """Initialize Sentry for error tracking"""
    enable_telemetry = os.getenv("AGENTIFYME_ENABLE_TELEMETRY")
    sentry_dsn = os.getenv("AGENTIFYME_SENTRY_DSN")
    environment = os.getenv("AGENTIFYME_ENV")
    if enable_telemetry and sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            release=str(__version__),
            environment=environment,
            send_default_pii=False,
            attach_stacktrace=True,
            enable_tracing=True,
            propagate_traces=True,
        )


async def run():
    """Entry point for the worker service"""
    try:
        api_gateway_url = get_env("AGENTIFYME_API_GATEWAY_URL")
        api_key = get_env("AGENTIFYME_API_KEY")
        agentifyme_env = get_env("AGENTIFYME_ENV")
        project_id = get_env("AGENTIFYME_PROJECT_ID")
        deployment_id = get_env("AGENTIFYME_DEPLOYMENT_ID")
        worker_id = get_env("AGENTIFYME_WORKER_ID")
        otel_endpoint = get_env("AGENTIFYME_OTEL_ENDPOINT")
        agentifyme_project_dir = get_env("AGENTIFYME_PROJECT_DIR", Path.cwd().as_posix())
        agentifyme_version = get_package_version("agentifyme")

        callback_handler = CallbackHandler()

        # Setup telemetry
        setup_telemetry(
            otel_endpoint,
            agentifyme_env,
            agentifyme_version,
        )

        # Add instrumentation to workflows and tasks
        auto_instrument(agentifyme_project_dir, callback_handler)

        logger.info(f"Starting Agentifyme service with worker {worker_id} and deployment {deployment_id}")

        await init_worker_service(
            api_gateway_url,
            api_key,
            project_id,
            deployment_id,
            worker_id,
            callback_handler,
        )

    except ValueError as e:
        logger.error(f"Worker service error: {e}")
        return 1
    except Exception as e:
        logger.error("Worker service error", exc_info=True, error=str(e))
        logger.exception(e)
        return 1
    return 0


async def init_worker_service(
    api_gateway_url: str,
    api_key: str,
    project_id: str,
    deployment_id: str,
    worker_id: str,
    callback_handler: CallbackHandler,
):
    grpc_options = [
        ("grpc.keepalive_time_ms", 60000),
        ("grpc.keepalive_timeout_ms", 20000),
        ("grpc.keepalive_permit_without_calls", True),
        ("grpc.enable_retries", 1),
    ]

    try:
        api_key_interceptor = APIKeyInterceptor(api_key)
        async with grpc.aio.insecure_channel(
            target=api_gateway_url,
            options=grpc_options,
            interceptors=[api_key_interceptor],
        ) as channel:
            stub = pb_grpc.GatewayServiceStub(channel)
            worker_service = WorkerService(
                stub,
                callback_handler,
                api_gateway_url,
                project_id,
                deployment_id,
                worker_id,
            )
            await worker_service.start_service()
    except KeyboardInterrupt:
        logger.info("Worker service stopped by user", exc_info=True)
    except Exception as e:
        logger.error("Worker service error", exc_info=True, error=str(e))
        raise
    finally:
        await worker_service.stop_service()


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if not value:
        if default is None:
            raise ValueError(f"{key} is not set")
        logger.warning(f"{key} is not set, using default: {default}")
        return default
    return value


def get_package_version(package_name: str):
    try:
        package_version = version(package_name)
        logger.info(f"{package_name} version: {package_version}")
    except PackageNotFoundError:
        logger.error(f"Package version for {package_name} not found")
        sys.exit(1)


def load_modules(project_dir: str):
    # WorkflowConfig.reset_registry()
    # TaskConfig.reset_registry()

    if not os.path.exists(project_dir):
        logger.warning(f"Project directory not found. Defaulting to working directory: {project_dir}")

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
