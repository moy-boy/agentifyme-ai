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
    CUSTOM = "CUSTOM"


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
        error_code: str | None = None,
        category: ErrorCategory | None = None,
        context: ErrorContext | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ):
        self.message = message
        self.error_code = error_code
        self.category = category
        self.context = context
        self.severity = severity
        self._traceback = traceback.format_exc()
        super().__init__(message)

    @property
    def traceback(self) -> str:
        return str(self._traceback)

    def __str__(self) -> str:
        category_str = self.category.value if self.category else "AgentifyMe"

        if self.context:
            component_type = self.context.component_type
            component_id = self.context.component_id
            return f"{category_str} Error in {component_type} [{component_id}]: {self.message}"

        return f"{category_str} Error: {self.message}"

    def __dict__(self) -> dict:
        return {
            "message": str(self.message),
            "error_code": str(self.error_code) if self.error_code else None,
            "category": str(self.category.value) if self.category else None,
            "component_type": str(self.context.component_type) if self.context else None,
            "component_id": str(self.context.component_id) if self.context else None,
            "severity": str(self.severity.value),
            "traceback": self.traceback,
        }


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
