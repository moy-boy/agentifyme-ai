import time
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

import orjson
from pydantic import BaseModel, Field, field_validator

from agentifyme.ml.llm.base import LLMResponseError

T = TypeVar("T")


class ReflectionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    FAILED = "failed"
    PARTIAL = "partial"


class ReflectionConfig(BaseModel):
    """Configuration for reflection behavior"""

    max_attempts: int = Field(
        default=2, ge=1, le=5, description="Maximum number of reflection attempts"
    )
    prompt_template: Optional[str] = Field(
        default=None, description="Custom prompt template for reflection"
    )
    error_formatter: Optional[str] = Field(
        default=None, description="Custom error formatting template"
    )
    success_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for successful reflection",
    )
    timeout_seconds: float = Field(
        default=30.0, ge=1.0, description="Maximum time for reflection process"
    )


class ReflectionLog(BaseModel):
    """Structured logging for reflection process"""

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    attempt: int
    message: str
    error: Optional[str] = None
    status: ReflectionStatus

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReflectionResult(BaseModel, Generic[T]):
    """Generic result type for reflection operations"""

    status: ReflectionStatus
    original_error: Optional[str] = Field(
        default=None, description="Original error that triggered reflection"
    )
    reflection_logs: list[ReflectionLog] = Field(
        default_factory=list, description="Detailed log of reflection process"
    )
    final_result: Optional[T] = Field(
        default=None, description="Final result after reflection"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score of the result"
    )
    execution_time: float = Field(
        default=0.0, ge=0.0, description="Total execution time in seconds"
    )

    @field_validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return round(v, 4)

    def add_log(
        self,
        attempt: int,
        message: str,
        error: Optional[str] = None,
        status: ReflectionStatus = ReflectionStatus.PARTIAL,
    ) -> None:
        """Add a new log entry"""
        self.reflection_logs.append(
            ReflectionLog(attempt=attempt, message=message, error=error, status=status)
        )

    @property
    def latest_log(self) -> Optional[ReflectionLog]:
        """Get the most recent log entry"""
        return self.reflection_logs[-1] if self.reflection_logs else None

    class Config:
        arbitrary_types_allowed = True


class ReflectionMixin:
    """Mixin providing reflection capabilities"""

    def __init__(self, reflection_config: Optional[ReflectionConfig] = None):
        self.reflection_config = reflection_config or ReflectionConfig()
        self._result: Optional[ReflectionResult] = None
        self._start_time: Optional[float] = None

    def _get_reflection_prompt(self) -> str:
        """Default reflection prompt template"""
        return """
        # Data Extraction Reflection
        The previous attempt to extract structured data encountered validation errors.
        Let's analyze and fix these issues.

        # Target Schema
        {schema}

        # Previous Extraction Attempt
        {previous_attempt}

        # Validation Errors
        {error_details}

        # Instructions
        1. Analyze why the extracted data failed validation
        2. Identify each field that needs correction
        3. Provide a new JSON response that exactly matches the schema

        Requirements:
        - Include all required fields
        - Match data types exactly as specified
        - Ensure nested structures are correct
        - Use exact field names from schema
        - Validate all constraints

        # Corrected JSON Response
        Provide the corrected JSON below:
        """

    async def reflect_and_correct(
        self,
        schema: dict[str, Any],
        previous_attempt: Any,
        error: Exception,
        correction_handler: callable,
    ) -> ReflectionResult:
        """Execute reflection process"""
        self._result = ReflectionResult(
            status=ReflectionStatus.PARTIAL, original_error=str(error)
        )
        self._start_time = time.time()

        self._result.add_log(
            attempt=0,
            message="Initial attempt failed",
            error=str(error),
            status=ReflectionStatus.PARTIAL,
        )

        for attempt in range(self.reflection_config.max_attempts):
            try:
                if (
                    time.time() - self._start_time
                ) > self.reflection_config.timeout_seconds:
                    raise TimeoutError("Reflection process exceeded maximum time")

                reflection_prompt = (
                    self.reflection_config.prompt_template
                    or self._get_reflection_prompt()
                ).format(
                    schema=orjson.dumps(schema, option=orjson.OPT_INDENT_2).decode(),
                    previous_attempt=str(previous_attempt),
                    error_details=str(error),
                )

                reflection_response = await self.json_extractor_task.language_model.generate_from_prompt_async(
                    reflection_prompt
                )

                if reflection_response.message is None:
                    raise LLMResponseError("No response received during reflection")

                corrected_result = await correction_handler(reflection_response.message)

                self._result.status = ReflectionStatus.SUCCESS
                self._result.final_result = corrected_result
                self._result.confidence = 1.0
                self._result.add_log(
                    attempt=attempt + 1,
                    message="Reflection succeeded",
                    status=ReflectionStatus.SUCCESS,
                )

                return self._result

            except Exception as reflect_error:
                self._result.add_log(
                    attempt=attempt + 1,
                    message="Reflection attempt failed",
                    error=str(reflect_error),
                    status=ReflectionStatus.PARTIAL,
                )
                error = reflect_error

        self._result.status = ReflectionStatus.FAILED
        self._result.execution_time = time.time() - self._start_time
        return self._result
