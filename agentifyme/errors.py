import sys
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
        execution_state: dict[str, Any] | None = None,
        error_type: type[Exception] | str = "AgentifyMeError",
        tb: str | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.category = category
        self.context = context
        self.severity = severity
        self.execution_state = execution_state
        self._error_type = error_type

        if tb is not None and tb != "":
            self._tb = tb
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()

            if error_type is None and exc_type is not None:
                self._error_type = exc_type

            if exc_traceback:
                self._tb = "".join(traceback.format_tb(exc_traceback))
            else:
                self._tb = "".join(traceback.format_stack())

        super().__init__(message)

    @property
    def traceback(self) -> str:
        return str(self._tb)

    @property
    def error_type(self) -> str:
        return str(self._error_type.__name__) if isinstance(self._error_type, type) else str(self._error_type) if self._error_type else ""

    def __str__(self) -> str:
        try:
            category_str = self.category.value if self.category else "AgentifyMe"
            if self.context and hasattr(self.context, "component_type") and hasattr(self.context, "component_id"):
                return f"{category_str} Error in {self.context.component_type} [{self.context.component_id}]: {self.message}"
            return f"{category_str} Error: {self.message}"
        except Exception:
            return f"Error: {self.message}"

    def __dict__(self) -> dict:
        return {
            "message": str(self.message),
            "error_code": str(self.error_code) if self.error_code else None,
            "category": str(self.category.value) if self.category else None,
            "component_type": str(self.context.component_type) if self.context else None,
            "component_id": str(self.context.component_id) if self.context else None,
            "severity": str(self.severity.value) if self.severity else None,
            "traceback": str(self._tb),
            "execution_state": self.execution_state,
            "error_type": self.error_type,
        }

    @property
    def as_dict(self) -> dict:
        return {
            "message": str(self.message),
            "error_code": str(self.error_code) if self.error_code else None,
            "category": str(self.category.value) if self.category else None,
            "severity": str(self.severity.value) if self.severity else None,
            "traceback": str(self._tb),
            "error_type": self.error_type,
        }


class AgentifyMeTimeoutError(AgentifyMeError):
    """Raised when any operation exceeds its time limit"""

    def __init__(self, message: str, context: ErrorContext, timeout_duration: float):
        super().__init__(message, ErrorCategory.TIMEOUT, context)
        self.timeout_duration = timeout_duration


class AgentifyMeValidationError(AgentifyMeError):
    """Raised when validation fails for any component"""

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        *,
        category: ErrorCategory = ErrorCategory.VALIDATION,
        error_code: str | None = "VALIDATION_ERROR",
        execution_state: dict[str, Any] | None = None,
        validation_details: dict[str, Any] | None = None,
    ):
        self.validation_details = validation_details
        super().__init__(
            message=message,
            error_code=error_code,
            category=category,
            context=context,
            execution_state=execution_state,
        )


class AgentifyMeExecutionError(AgentifyMeError):
    """Raised when execution fails for any component"""

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        *,
        category: ErrorCategory = ErrorCategory.EXECUTION,
        error_code: str | None = None,
        execution_state: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=category,
            context=context,
            execution_state=execution_state,
        )

    def __str__(self) -> str:
        error_prefix = f"[{self.error_type.__name__}]" if self.error_type else ""
        return f"{error_prefix} {super().__str__()}"
