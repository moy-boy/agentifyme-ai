from typing import Optional

import structlog


class BaseLogger:
    _instance: Optional["BaseLogger"] = None
    _logger: Optional[structlog.BoundLogger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BaseLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, logger: structlog.BoundLogger):
        if cls._logger is None:
            cls._logger = logger
        else:
            print("Warning: Logger was already initialized. Ignoring this call.")

    @classmethod
    def get_logger(cls) -> structlog.BoundLogger:
        if cls._logger is None:
            raise RuntimeError(
                "Logger has not been initialized. Call BaseLogger.initialize() first."
            )
        return cls._logger

    @classmethod
    def configure(cls):
        """
        Configure the basic structlog logger.
        Override this method to customize the logger configuration.
        """
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.BoundLogger,
            logger_factory=structlog.PrintLoggerFactory(),
        )
        logger = structlog.get_logger()
        cls.initialize(logger)


# Convenience function
def get_logger() -> structlog.BoundLogger:
    if BaseLogger._logger is None:
        BaseLogger.configure()
    return BaseLogger.get_logger()
