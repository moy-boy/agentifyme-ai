import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from inspect import signature
from typing import Any, ClassVar

from loguru import logger

from agentifyme.errors import (
    AgentifyMeError,
    AgentifyMeValidationError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
)


@dataclass
class BaseConfig:
    """Base configuration class."""

    name: str | None = None
    slug: str | None = None
    description: str | None = None
    func: Callable[..., Any] | None = None
    _registry: ClassVar[dict[str, "BaseComponent"]] = {}

    @classmethod
    def register(cls, component: "BaseComponent"):
        """Register a component in the registry.

        Args:
            component (BaseComponent): The component to register.

        """
        name = component.config.name
        if name is None:
            name = re.sub(r"(?<!^)(?=[A-Z])", "_", component.__class__.__name__).lower()

        name = "-".join(name.lower().split())

        if name and name not in cls._registry:
            cls._registry[name] = component

    @classmethod
    def reset_registry(cls):
        """Reset the registry."""
        cls._registry = {}

    @classmethod
    def get(cls, name: str) -> "BaseComponent":
        """Get a component from the registry.

        Args:
            name (str): The name of the component to get.

        Returns:
            BaseComponent: The component.

        Raises:
            AgentifyMeError: If the component is not found in the registry.

        """
        base_module = cls._registry.get(name)
        if base_module is None:
            raise AgentifyMeError(message=f"Component {name} not found in registry.", error_code="COMPONENT_NOT_FOUND")
        return base_module

    @classmethod
    def get_all(cls) -> list[str]:
        """Get all the components in the registry.

        Returns:
            list[str]: The names of the components.

        """
        return list(cls._registry.keys())

    @classmethod
    def get_registry(cls) -> dict[str, "BaseComponent"]:
        """Get the registry.

        Returns:
            dict[str, BaseComponent]: The registry.

        """
        return cls._registry


@dataclass
class BaseComponent(ABC):
    """Base class for components in the agentifyme framework."""

    component_type: str
    config: BaseConfig

    def __call__(self, *args, **kwargs: Any) -> Any:
        with self:
            return self.run(*args, **kwargs)

    @contextmanager
    def error_context(self, kwargs):
        try:
            yield
        except AgentifyMeError:
            raise
        except Exception as e:
            error_type = type(e).__name__ or "Error"
            raise AgentifyMeError(
                message=str(e),
                context=ErrorContext(component_type=self.__class__.__name__.lower(), component_id=self.config.name),
                execution_state=dict(kwargs),
                category=ErrorCategory.EXECUTION,
                severity=ErrorSeverity.ERROR,
                error_type=error_type,
            ) from e


class RunnableComponent(BaseComponent):
    """Base class for components that can be run."""

    def __init__(self, component_type: str, config: BaseConfig, *args, **kwargs) -> None:
        super().__init__(component_type=component_type, config=config, *args, **kwargs)

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

    def _validate_arguments(self, prepared_kwargs: dict[str, Any]) -> None:
        """Validate keyword arguments against function signature."""
        if not self.config.func:
            return

        sig = signature(self.config.func)
        try:
            sig.bind(**prepared_kwargs)
        except TypeError as e:
            raise AgentifyMeValidationError(
                message=f"Invalid arguments for workflow {self.config.name}: {e!s}",
                error_code="INVALID_ARGUMENTS",
                category=ErrorCategory.VALIDATION,
                context=ErrorContext(component_type="workflow", component_id=self.config.name),
                execution_state=dict(prepared_kwargs),
            )

    def _prepare_kwargs(self, args: tuple, kwargs: dict) -> dict:
        prepared_kwargs = kwargs.copy()
        if self.config.func:
            prepared_kwargs.update(zip(self.config.func.__code__.co_varnames, args, strict=False))
        self._validate_arguments(prepared_kwargs)
        return prepared_kwargs
