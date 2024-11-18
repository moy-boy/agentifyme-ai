from typing import Any

from agentifyme.config import BaseConfig, BaseModule


class TriggerError(Exception):
    pass


class TriggerConfig(BaseConfig):
    """
    Represents the configuration for a workflow trigger
    """

    pass


class Trigger(BaseModule):
    def __init__(self, config: TriggerConfig, *args, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.config = config

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self.config.func:
            kwargs.update(zip(self.config.func.__code__.co_varnames, args))
            return self.config.func(**kwargs)

        raise TriggerError("No function defined for trigger")
