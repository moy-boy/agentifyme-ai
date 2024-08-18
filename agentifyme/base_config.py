import asyncio
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Coroutine, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict


class AgentifyMeError(Exception):
    """Base exception class for agentifyme."""

    pass


class BaseConfig(BaseModel):
    """Base configuration class."""

    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    func: Optional[Callable[..., Any]] = None
    _registry: ClassVar[Dict[str, "BaseModule"]] = {}

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
