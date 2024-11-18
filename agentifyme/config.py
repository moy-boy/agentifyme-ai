import re
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Callable, ClassVar, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator

from agentifyme.utilities.func_utils import (
    Param,
    timedelta_to_cron,
)


class AgentifyMeError(Exception):
    """Base exception class for agentifyme."""

    pass


class BaseConfig(BaseModel):
    """Base configuration class."""

    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    func: Optional[Callable[..., Any]] = None
    _registry: ClassVar[dict[str, "BaseModule"]] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def register(cls, module: "BaseModule"):
        """
        Register a module in the registry.

        Args:
            module (BaseModule): The module to register.

        """
        name = module.config.name
        if name is None:
            name = re.sub(r"(?<!^)(?=[A-Z])", "_", module.__class__.__name__).lower()

        name = "-".join(name.lower().split())

        if name and name not in cls._registry:
            cls._registry[name] = module

    @classmethod
    def reset_registry(cls):
        """
        Reset the registry.

        """
        cls._registry = {}

    @classmethod
    def get(cls, name: str) -> "BaseModule":
        """
        Get a module from the registry.

        Args:
            name (str): The name of the module to get.

        Returns:
            BaseModule: The module.

        Raises:
            AgentifyMeError: If the module is not found in the registry.
        """
        base_module = cls._registry.get(name)
        if base_module is None:
            raise AgentifyMeError(f"Module {name} not found in registry.")
        return base_module

    @classmethod
    def get_all(cls) -> list[str]:
        """
        Get all the modules in the registry.

        Returns:
            list[str]: The names of the modules.
        """
        return list(cls._registry.keys())

    @classmethod
    def get_registry(cls) -> dict[str, "BaseModule"]:
        """
        Get the registry.

        Returns:
            dict[str, BaseModule]: The registry.
        """
        return cls._registry


class BaseModule(ABC):
    """Base class for modules in the agentifyme framework."""

    name = None

    def __init__(self, config: BaseConfig, **kwargs: Any):
        self.config = config

    def __call__(self, *args, **kwargs: Any) -> Any:
        with self:
            return self.run(*args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def run(self, *args, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def arun(self, *args, **kwargs: Any) -> Any:
        raise NotImplementedError


class TaskConfig(BaseConfig):
    """
    Represents the configuration for a task.

    Attributes:
        name (str): The name of the task.
        description (str): The description of the task.
        objective (Optional[str]): The objective of the task.
        instructions (Optional[str]): The instructions for completing the task.
        tools (Optional[list[Tool]]): The list of tools required for the task.
        input_params (list[Param]): The list of input parameters for the task.
        output_params (list[Param]): The list of output parameters for the task.
    """

    objective: Optional[str] = None
    instructions: Optional[str] = None
    # tools: Optional[list[Tool]]
    input_parameters: dict[str, Param]
    output_parameters: list[Param]


class WorkflowConfig(BaseConfig):
    """
    Represents a workflow.

    Attributes:
        name (str): The name of the workflow.
        slug (str): The slug of the workflow.
        description (Optional[str]): The description of the workflow (optional).
        func (Callable[..., Any]): The function associated with the workflow.
        input_parameters (dict[str, Param]): A dictionary of input parameters for the workflow.
        output_parameters (list[Param]): The list of output parameters for the workflow.
        schedule (Optional[Union[str, timedelta]]): The schedule for the workflow.
            Can be either a cron expression string or a timedelta object.
    """

    input_parameters: dict[str, Param]
    output_parameters: list[Param]
    schedule: Optional[Union[str, timedelta]]

    @field_validator("schedule")
    @classmethod
    def normalize_schedule(cls, v: Optional[Union[str, timedelta]]) -> Optional[str]:
        if isinstance(v, timedelta):
            try:
                return timedelta_to_cron(v)
            except ValueError as e:
                raise ValueError(
                    f"Cannot convert this timedelta to a cron expression: {e}"
                )
        return v  # Return as-is if it's already a string or None


class AgentifyMeConfig(BaseModel):
    task_registry: ClassVar[dict[str, BaseModel]] = {}
    workflow_registry: ClassVar[dict[str, BaseModel]] = {}

    @classmethod
    def register_task(cls, task: TaskConfig):
        cls.task_registry[task.name] = task

    @classmethod
    def register_workflow(cls, workflow: WorkflowConfig):
        cls.workflow_registry[workflow.name] = workflow

    @classmethod
    def get_task(cls, task_name: str) -> TaskConfig:
        return cls.task_registry.get(task_name)

    @classmethod
    def get_workflow(cls, workflow_name: str) -> WorkflowConfig:
        return cls.workflow_registry.get(workflow_name)

    @classmethod
    def list_tasks(cls):
        print("Tasks:")
        for k, task in cls.task_registry.items():
            print(f"  - {k}: {task.description}")
        return cls.task_registry.keys()

    @classmethod
    def list_workflows(cls):
        print("Workflows:")
        for k, workflow in cls.workflow_registry.items():
            print(f"  - {k}: {workflow.description}")
        return cls.workflow_registry.keys()
