from typing import Generic, Mapping, TypeVar, Union


class ToolExecutionError(Exception):
    pass


ToolInputType = TypeVar("ToolInputType")
ToolOutputType = TypeVar("ToolOutputType")


class Tool(Generic[ToolInputType, ToolOutputType]):
    """Base class for all tools."""

    name: str
    description: str
    inputs: ToolInputType
    output: ToolOutputType

    def __init__(self) -> None:
        pass

    def __call__(
        self, *args, **kwargs
    ) -> Union[ToolOutputType, Mapping[str, ToolOutputType]]:
        return self.run(*args, **kwargs)

    def run(
        self, *args, **kwargs
    ) -> Union[ToolOutputType, Mapping[str, ToolOutputType]]:
        """Run the tool with the given input and return the output."""
        raise NotImplementedError

    async def async_run(
        self, *args, **kwargs
    ) -> Union[ToolOutputType, Mapping[str, ToolOutputType]]:
        """Run the tool with the given input and return the output."""
        raise NotImplementedError

    class Config:
        """Pydantic configuration."""

        frozen = True
        arbitrary_types_allowed = True
        validate_assignment = True
        validate_all = True
