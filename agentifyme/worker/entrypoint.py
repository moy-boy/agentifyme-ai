import asyncio
import os
import sys
import traceback
from pathlib import Path

import grpc
from dotenv import load_dotenv
from importlib_metadata import PackageNotFoundError, version
from loguru import logger

import agentifyme.worker.pb.api.v1.gateway_pb2_grpc as pb_grpc
from agentifyme.tasks import TaskConfig
from agentifyme.utilities.modules import (
    load_modules_from_directory,
)
from agentifyme.worker.auth_interceptor import APIKeyInterceptor
from agentifyme.worker.telemetry import (
    auto_instrument,
    setup_telemetry,
)
from agentifyme.worker.worker_service import WorkerService
from agentifyme.workflows import WorkflowConfig


def main():
    asyncio.run(run())


async def run():
    """Entry point for the worker service"""
    try:
        if Path(".env.worker").exists():
            logger.info("Loading worker environment variables")
            load_dotenv(Path(".env.worker"))

        api_gateway_url = get_env("AGENTIFYME_API_GATEWAY_URL")
        api_key = get_env("AGENTIFYME_API_KEY")
        agentifyme_env = get_env("AGENTIFYME_ENV")
        project_id = get_env("AGENTIFYME_PROJECT_ID")
        deployment_id = get_env("AGENTIFYME_DEPLOYMENT_ID")
        worker_id = get_env("AGENTIFYME_WORKER_ID")
        agentifyme_project_dir = get_env("AGENTIFYME_PROJECT_DIR", Path.cwd().as_posix())
        agentifyme_version = get_package_version("agentifyme")
        otel_endpoint = get_env("AGENTIFYME_OTEL_ENDPOINT")

        # Setup telemetry
        setup_telemetry(
            otel_endpoint,
            agentifyme_env,
            agentifyme_version,
        )

        # Add instrumentation to workflows and tasks
        auto_instrument(agentifyme_project_dir)

        logger.info(
            "Starting Agentifyme service",
            env=agentifyme_env,
            project_dir=agentifyme_project_dir,
            deployment_id=deployment_id,
        )

        await init_worker_service(api_gateway_url, api_key, project_id, deployment_id, worker_id)

    except ValueError as e:
        logger.error(f"Worker service error: {e}")
        traceback.print_exc()
        return 1
    except KeyboardInterrupt:
        logger.info("Worker service stopped by user", exc_info=True)
    except Exception as e:
        logger.error("Worker service error", exc_info=True, error=str(e))
        traceback.print_exc()
        return 1
    return 0


async def init_worker_service(api_gateway_url: str, api_key: str, project_id: str, deployment_id: str, worker_id: str):
    grpc_options = [
        ("grpc.keepalive_time_ms", 60000),
        ("grpc.keepalive_timeout_ms", 20000),
        ("grpc.keepalive_permit_without_calls", True),
        ("grpc.enable_retries", 1),
    ]

    try:
        api_key_interceptor = APIKeyInterceptor(api_key)
        # , interceptors=[api_key_interceptor]
        async with grpc.aio.insecure_channel(target=api_gateway_url, options=grpc_options, interceptors=[api_key_interceptor]) as channel:
            stub = pb_grpc.GatewayServiceStub(channel)
            worker_service = WorkerService(stub, api_gateway_url, project_id, deployment_id, worker_id)
            await worker_service.start_service()
            # start worker stream
            await worker_service.start_worker_stream()
    except KeyboardInterrupt:
        logger.info("Worker service stopped by user", exc_info=True)
    except Exception as e:
        logger.error("Worker service error", exc_info=True, error=str(e))
        traceback.print_exc()
        raise e
    finally:
        await worker_service.stop_service()


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if not value:
        if default is None:
            raise ValueError(f"{key} is not set")
        else:
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
    WorkflowConfig.reset_registry()
    TaskConfig.reset_registry()

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
