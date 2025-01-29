import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import orjson
from loguru import logger

from agentifyme.components.task import TaskConfig
from agentifyme.components.workflow import WorkflowConfig
from agentifyme.worker.telemetry import setup_telemetry
from agentifyme.worker.telemetry.instrumentor import OTELInstrumentor


def write_config_file(config, file_path):
    """Write the given configuration dictionary to a file.

    Args:
        config (dict): The configuration dictionary to write.
        file_path (str): The path to the file where the configuration will be written.

    Returns:
        None

    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(orjson.dumps(config, default=str))


def signal_steady_state():
    with open("/tmp/steady_state.signal", "w") as f:
        f.write("STEADY_STATE_REACHED")


def initialize_workflows():
    working_directory = os.getcwd()
    temp_dir = os.path.join(working_directory, ".agentifyme")

    try:
        os.makedirs(temp_dir, exist_ok=True)
        config_dir = os.path.join(temp_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
    except OSError:
        # If we don't have permission, use the home directory
        home_dir = str(Path.home())
        temp_dir = os.path.join(home_dir, ".agentifyme")
        os.makedirs(temp_dir, exist_ok=True)
        config_dir = os.path.join(temp_dir, "config")
        os.makedirs(config_dir, exist_ok=True)

    try:
        # save the tasks configuration
        tasks_config = []
        for task_name, task in TaskConfig.get_registry().items():
            logger.info(f"Generating task configuration for {task_name}", task_name=task_name)
            task_config = task.config.model_dump(exclude={"func"}, exclude_unset=True, exclude_none=True)
            task_slug = task_config.get("name", "").replace(" ", "-").replace("_", "-").lower()
            task_config["slug"] = task_slug
            tasks_config.append(task_config)
        write_config_file(tasks_config, os.path.join(config_dir, "tasks.json"))

        # save the workflows configuration
        workflows_config = []
        for workflow_name, workflow in WorkflowConfig.get_registry().items():
            logger.info(
                f"Generating workflow configuration for {workflow_name}",
                workflow_name=workflow_name,
            )
            workflow_config = workflow.config.model_dump(exclude={"func"}, exclude_unset=True, exclude_none=True)
            workflow_slug = workflow_config.get("slug", "").replace(" ", "-").replace("_", "-").lower()
            workflow_config["slug"] = workflow_slug
            workflows_config.append(workflow_config)
        write_config_file(workflows_config, os.path.join(config_dir, "workflows.json"))
        logger.info(
            f"Successfully loaded workflows and tasks configuration from {config_dir}",
            config_dir=config_dir,
        )

        # Get the deployment ID
        deployment_id = os.getenv("AGENTIFYME_DEPLOYMENT_ID")
        if deployment_id is None:
            raise ValueError("AGENTIFYME_DEPLOYMENT_ID is not set")

        # Get the replica ID
        replica_id = os.getenv("AGENTIFYME_REPLICA_ID")
        if replica_id is None:
            raise ValueError("AGENTIFYME_REPLICA_ID is not set")

        logger.info(
            f"Worker started for deployment {deployment_id} with worker id {replica_id}",
            deployment_id=deployment_id,
            replica_id=replica_id,
        )
    except Exception as e:
        logger.error(f"WorfklowError {e}")
        sys.exit(1)


def bootstrap():
    agentifyme_worker_version = None
    agentifyme_version = None

    try:
        agentifyme_version = version("agentifyme")
        logger.info(f"Agentifyme version: {agentifyme_version}")
    except PackageNotFoundError:
        logger.error("Package version not found")
        sys.exit(1)

    try:
        agentifyme_worker_version = version("agentifyme-worker")
        logger.info(f"Agentifyme-worker version: {agentifyme_worker_version}")
    except PackageNotFoundError:
        logger.error("Package version not found")
        sys.exit(1)

    _env = os.getenv("AGENTIFYME_ENV", "unknown")
    _project_dir = os.getenv("AGENTIFYME_PROJECT_DIR", "unknown")

    try:
        setup_telemetry(_env, agentifyme_worker_version)
        logger.info("Initializing Agentifyme worker", env=_env, project_dir=_project_dir)
        OTELInstrumentor.instrument()
        initialize_workflows()
    except Exception as e:
        logger.error(f"WorfklowError {e}")
        sys.exit(1)
