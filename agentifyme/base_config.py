import re
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Optional, Union

from pydantic import BaseModel


class AgentifyMeError(Exception):
    """Base exception class for agentifyme."""

    pass


class BaseConfig(BaseModel):
    """Base configuration class."""

    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    func: Union[Callable[..., Any], None] = None
    _registry: ClassVar[Dict[str, "BaseModule"]] = {}

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

        """

        base_module = cls._registry.get(name)
        if base_module is None:
            raise AgentifyMeError(f"Module {name} not found in registry.")

        return base_module


class BaseModule(ABC):
    """
    Base class for modules in the agentifyme framework.
    """

    name = None

    def __init__(self, config: BaseConfig, **kwargs: Any):
        self.config = config

    def __call__(self, *args, **kwargs: Any):
        return self.run(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def run(self, *args, **kwargs: Any):
        raise NotImplementedError
