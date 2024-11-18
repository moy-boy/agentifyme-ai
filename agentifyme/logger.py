from loguru import logger

from agentifyme.utilities.annotations import deprecated


# Deprecated: Convenience function migrated to use loguru logger instead of structlog.
@deprecated(
    "Use loguru logger `from loguru import logger` directly instead of this convenience function."
)
def get_logger():
    return logger
