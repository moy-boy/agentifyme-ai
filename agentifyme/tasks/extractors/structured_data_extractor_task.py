import warnings
from typing import Any, Dict, Optional, Type, Union

import orjson
from pydantic import BaseModel, ValidationError

from agentifyme.ml.llm import LanguageModelConfig, LanguageModelType
from agentifyme.tasks.extractors.json_data_extractor_task import (
    JSONDataExtractorTask,
    JSONParsingError,
)
from agentifyme.tasks.reflection import (
    ReflectionConfig,
    ReflectionMixin,
    ReflectionResult,
)
from agentifyme.tasks.task import Task, TaskConfig
from agentifyme.utilities.func_utils import Param


class StructuredDataExtractorTask(Task, ReflectionMixin):
    """
    Extracts structured data from text using LLMs with reflection capabilities for error correction.
    """

    def __init__(
        self,
        config: Optional[TaskConfig] = None,
        output_schema: Optional[Union[str, Dict[str, str]]] = None,
        language_model: Optional[Union[LanguageModelType, str]] = None,
        language_model_config: Optional[LanguageModelConfig] = None,
        prompt_template: Optional[str] = None,
        max_retries: int = 3,
        reflection_config: Optional[ReflectionConfig] = None,
        **kwargs,
    ) -> None:
        Task.__init__(self, config, **kwargs)
        ReflectionMixin.__init__(self, reflection_config)

        if config is None:
            config = TaskConfig(
                name="Structured Data Extractor",
                description="Extracts structured data from text with reflection capabilities.",
                input_parameters={
                    "text": Param(
                        name="text",
                        data_type="str",
                        description="The text to extract data from.",
                    )
                },
                output_parameters=[
                    Param(
                        name="json",
                        data_type="str",
                        description="The extracted structured data.",
                    )
                ],
            )

        self.config = config
        self.output_schema = output_schema
        self.prompt_template = prompt_template
        self.max_retries = max_retries

        self.json_extractor_task = JSONDataExtractorTask(
            config=TaskConfig(
                name="JSON Data Extractor",
                description="Extracts a JSON object from text.",
                input_parameters={
                    "text": Param(
                        name="text",
                        data_type="str",
                        description="The text to extract JSON from.",
                    )
                },
                output_parameters=[
                    Param(
                        name="json",
                        data_type="str",
                        description="The extracted JSON object.",
                    )
                ],
            ),
            language_model=language_model,
            language_model_config=language_model_config,
        )

    def _validate_and_parse_data(
        self, json_data: Dict[str, Any], output_type: Type[BaseModel]
    ) -> BaseModel:
        """Validate and parse extracted JSON data"""
        if isinstance(json_data, str):
            raise JSONParsingError("No JSON object found in the response")

        try:
            return output_type(**json_data)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append(f"Field '{location}': {error['msg']}")

            raise JSONParsingError(
                f"Data validation failed:\n"
                f"{chr(10).join(error_details)}\n\n"
                f"Schema: {output_type.model_json_schema()}\n"
                f"Data: {json_data}",
                None,  # No raw_errors attribute available
            ) from e

        except Exception as e:
            print(e)
            print(e.errors())

            raise e

    async def _extract_with_reflection(
        self, text: str, output_type: Type[BaseModel]
    ) -> Union[BaseModel, ReflectionResult]:
        """Extract data with reflection support"""
        try:
            output_schema = output_type.model_json_schema()
            json_data = await self.json_extractor_task.arun(
                text, output_schema=output_schema
            )
            return self._validate_and_parse_data(json_data, output_type)

        except (ValidationError, JSONParsingError) as e:

            async def correction_handler(reflection_response: str) -> BaseModel:
                corrected_json = self.json_extractor_task.extract_json(
                    reflection_response
                )
                if corrected_json is None:
                    raise JSONParsingError("Failed to extract JSON from reflection")
                return self._validate_and_parse_data(corrected_json, output_type)

            return await self.reflect_and_correct(
                schema=output_type.model_json_schema(),
                previous_attempt=json_data if "json_data" in locals() else {},
                error=e,
                correction_handler=correction_handler,
            )

    async def arun(
        self, input_data: Union[str, Dict[str, Any]], output_type: Type[BaseModel]
    ) -> Union[BaseModel, ReflectionResult]:
        """Async execution with reflection support"""
        text = (
            input_data
            if isinstance(input_data, str)
            else orjson.dumps(input_data, option=orjson.OPT_INDENT_2).decode()
        )

        return await self._extract_with_reflection(text, output_type)

    def run(
        self, input_data: Union[str, Dict[str, Any]], output_type: Type[BaseModel]
    ) -> Union[BaseModel, ReflectionResult]:
        """Synchronous execution with reflection support"""
        import asyncio

        return asyncio.run(self.arun(input_data, output_type))


class PydanticDataExtractorTask(StructuredDataExtractorTask):
    def __init__(self, *args, **kwargs) -> None:
        warnings.warn(
            "PydanticDataExtractorTask is deprecated. Use StructuredDataExtractorTask instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
