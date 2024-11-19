import asyncio
import os
import sys
import traceback
from pathlib import Path

from importlib_metadata import PackageNotFoundError, version
from loguru import logger

from agentifyme.config import TaskConfig, WorkflowConfig
from agentifyme.utilities.modules import (
    load_modules_from_directory,
)
from agentifyme.worker.telemetry import setup_telemetry
from agentifyme.worker.worker_service import run_worker_service


def run():
    """Entry point for the worker service"""
    try:
        agentifyme_env = os.getenv("AGENTIFYME_ENV", "unknown")

        current_working_dir = Path.cwd()
        agentifyme_project_dir = os.getenv(
            "AGENTIFYME_PROJECT_DIR", current_working_dir.as_posix()
        )

        agentifyme_version = get_package_version("agentifyme")
        setup_telemetry(
            agentifyme_env,
            agentifyme_version,
        )

        load_modules(agentifyme_project_dir)
        # OTELInstrumentor.instrument()

        # List workflows
        for workflow_name in WorkflowConfig.get_all():
            logger.info(f"Workflow: {workflow_name}")

        logger.info(
            "Starting Agentifyme service",
            env=agentifyme_env,
            project_dir=agentifyme_project_dir,
        )
        asyncio.run(run_worker_service())

    except KeyboardInterrupt:
        logger.info("Worker service stopped by user", exc_info=True)
    except Exception as e:
        logger.error("Worker service error", exc_info=True)
        traceback.print_exc()
        return 1
    return 0


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
        logger.warning(
            f"Project directory not found. Defaulting to working directory: {project_dir}"
        )

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
