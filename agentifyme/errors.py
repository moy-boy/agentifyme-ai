import traceback
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ErrorCategory(Enum):
    """Categories of errors in the AgentifyMe system"""

    TIMEOUT = "TIMEOUT"
    VALIDATION = "VALIDATION"
    EXECUTION = "EXECUTION"
    RESOURCE = "RESOURCE"
    PERMISSION = "PERMISSION"
    CONFIGURATION = "CONFIGURATION"


class ErrorSeverity(Enum):
    """Enum to classify the severity of workflow errors"""

    FATAL = "FATAL"  # Unrecoverable errors
    ERROR = "ERROR"  # Serious errors that may be recoverable
    WARNING = "WARNING"  # Issues that don't stop execution but should be noted
    INFO = "INFO"  # Informational messages about error conditions


class ErrorContext(BaseModel):
    component_type: str
    component_id: str
    attributes: dict[str, Any] | None = {}
    trace_id: str | None = None
    run_id: str | None = None


class AgentifyMeError(Exception):
    """Base class for all AgentifyMe errors"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ):
        self.message = message
        self.category = category
        self.context = context
        self.severity = severity
        self.traceback = traceback.format_exc()
        super().__init__(message)

    def __str__(self):
        return f"{self.category.value} Error in {self.context.component_type} " f"[{self.context.component_id}]: {self.message}"


class AgentifyMeTimeoutError(AgentifyMeError):
    """Raised when any operation exceeds its time limit"""

    def __init__(self, message: str, context: ErrorContext, timeout_duration: float):
        super().__init__(message, ErrorCategory.TIMEOUT, context)
        self.timeout_duration = timeout_duration


class AgentifyMeValidationError(AgentifyMeError):
    """Raised when validation fails for any component"""

    def __init__(self, message: str, context: ErrorContext, validation_details: dict[str, Any]):
        super().__init__(message, ErrorCategory.VALIDATION, context)
        self.validation_details = validation_details


class AgentifyMeExecutionError(AgentifyMeError):
    """Raised when execution fails for any component"""

    def __init__(self, message: str, context: ErrorContext, execution_state: dict[str, Any]):
        super().__init__(message, ErrorCategory.EXECUTION, context)
        self.execution_state = execution_state
