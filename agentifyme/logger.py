from typing import Callable, List, Optional

import structlog


class BaseLogger:
    _instance: Optional["BaseLogger"] = None
    _logger: Optional[structlog.BoundLogger] = None
    _processors: List[Callable] = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BaseLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def configure(cls, additional_processors: List[Callable] = None):
        """
        Configure the structlog logger with the option to add additional processors.
        """
        processors = cls._processors.copy()
        if additional_processors:
            processors = additional_processors + processors

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.BoundLogger,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=False,  # Important: Disable caching
        )
        cls._logger = structlog.get_logger()

    @classmethod
    def get_logger(cls) -> structlog.BoundLogger:
        if cls._logger is None:
            cls.configure()
        return cls._logger

    @classmethod
    def add_processors(cls, processors: List[Callable]):
        """
        Add new processors to the logger configuration.
        """
        cls._processors = processors + cls._processors
        cls.configure()


# Convenience function
def get_logger() -> structlog.BoundLogger:
    return BaseLogger.get_logger()
