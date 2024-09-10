import logging
from typing import Callable, List, Optional

import structlog


class BaseLogger:
    _instance: Optional["BaseLogger"] = None
    _logger: Optional[structlog.BoundLogger] = None
    _processors: List[Callable] = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        # Remove JSONRenderer from here
    ]
    _handlers: List[logging.Handler] = []  # Start with an empty list

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BaseLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def configure(cls, additional_processors: List[Callable] = None):
        # if cls._logger is not None:
        #     return  # Already configured, skip

        processors = cls._processors.copy()
        if additional_processors:
            processors = additional_processors + processors

        structlog.configure(
            processors=processors
            + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add a single StreamHandler with ProcessorFormatter
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer()
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

        # Add custom handlers
        for custom_handler in cls._handlers:
            root_logger.addHandler(custom_handler)

        print(">> configuring logger")
        print(cls._handlers)
        print(cls._processors)
        cls._logger = structlog.get_logger()

    @classmethod
    def get_logger(cls) -> structlog.BoundLogger:
        if cls._logger is None:
            cls.configure()
        return cls._logger

    @classmethod
    def add_processors(cls, processors: List[Callable]):
        cls._processors = processors + cls._processors

    @classmethod
    def add_handlers(cls, handlers: List[logging.Handler]):
        cls._handlers.extend(handlers)


# Convenience function
def get_logger() -> structlog.BoundLogger:
    return BaseLogger.get_logger()
