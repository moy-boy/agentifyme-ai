import re
from typing import Any, Optional, Union

import orjson
from loguru import logger

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelType,
    get_language_model,
)
from agentifyme.tasks.task import Task, TaskConfig
from agentifyme.utilities.func_utils import Param


class JSONParsingError(Exception):
    pass


class InvalidJSONStructureError(Exception):
    pass


class LLMResponseError(Exception):
    pass


class JSONDataExtractorTask(Task):
    def __init__(
        self,
        config: Optional[TaskConfig] = None,
        output_schema: Optional[Union[str, dict[str, str]]] = None,
        language_model: Optional[Union[LanguageModelType, str]] = None,
        language_model_config: Optional[LanguageModelConfig] = None,
        prompt_template: Optional[str] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> None:
        Task.__init__(self, config, **kwargs)
        if config is None:
            config = TaskConfig(
                name="JSON Data Extractor",
                description="Extracts a JSON object from a given text.",
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
            )

        super().__init__(config, **kwargs)
        self.config = config
        self.output_schema = output_schema
        self.prompt_template = prompt_template
        self.max_retries = max_retries

        # Initialize the language model
        if language_model_config is not None:
            self.language_model_config = language_model_config
            self.language_model = get_language_model(language_model_config)

        elif language_model is not None:
            if isinstance(language_model, LanguageModelType):
                _language_model_config = LanguageModelConfig(model=language_model)
                self.language_model_config = _language_model_config
                self.language_model = get_language_model(_language_model_config)

            else:
                _language_model = LanguageModelType(language_model)
                _language_model_config = LanguageModelConfig(model=_language_model)
                self.language_model_config = _language_model_config
                self.language_model = get_language_model(_language_model_config)

        else:
            raise ValueError(
                "Either language_model or language_model_config must be provided"
            )

        if prompt_template is None:
            self.prompt_template = self.get_default_prompt()

    def extract_json(self, text: str) -> dict[str, Any] | None:
        """
        Extracts the first JSON object from the given text.

        Args:
            text (str): The input text containing JSON data.

        Returns:
            dict: The parsed JSON object, or None if no JSON object is found.
        """
        # Regular expression to match JSON objects
        json_pattern = re.compile(r"\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}")
        json_match = json_pattern.search(text)
        if json_match:
            try:
                # Parse the JSON object
                return orjson.loads(json_match.group())
            except orjson.JSONDecodeError:
                # If parsing fails, return None
                return None
        return None

    def get_default_prompt(self) -> str:
        return """

        # Objective
        Extract the structured data from the provided text.

        # Instructions
        Understand the data definition below, parse the objects from the provided text, and return the structured data in the JSON format.

        # Data Definition
        {output_schema}

        # Provided Text
        {text}

        Strictly extract the data provided in the data definition.
        """

    def run(
        self,
        text: str,
        output_schema: Optional[Union[str, dict[str, Any]]] = None,
    ) -> Union[str, dict[str, Any]]:
        output_schema = output_schema or self.output_schema
        if output_schema is None:
            raise ValueError("output_schema must be provided")

        if self.prompt_template is None:
            raise ValueError("prompt_template must be provided")

        for attempt in range(self.max_retries):
            try:
                prompt = self.prompt_template.format(
                    output_schema=output_schema,
                    text=text,
                )

                response = self.language_model.generate_from_prompt(prompt)

                if response.message is not None:
                    # Extract JSON from the response
                    json_data = self.extract_json(response.message)

                    if json_data is not None:
                        return json_data

                    # If no JSON is found, raise an error
                    raise JSONParsingError("No JSON object found in the response")

            except (JSONParsingError, LLMResponseError) as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        return "No JSON Found"

    async def arun(
        self,
        text: str,
        output_schema: Optional[Union[str, dict[str, Any]]] = None,
    ) -> Union[str, dict[str, Any]]:
        output_schema = output_schema or self.output_schema
        if output_schema is None:
            raise ValueError("output_schema must be provided")

        if self.prompt_template is None:
            raise ValueError("prompt_template must be provided")

        for attempt in range(self.max_retries):
            try:
                prompt = self.prompt_template.format(
                    output_schema=output_schema,
                    text=text,
                )

                response = await self.language_model.generate_from_prompt_async(prompt)

                if response.message is not None:
                    # Extract JSON from the response
                    json_data = self.extract_json(response.message)

                    if json_data is not None:
                        return json_data

                    # If no JSON is found, raise an error
                    raise JSONParsingError("No JSON object found in the response")

            except (JSONParsingError, LLMResponseError) as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        return "No JSON Found"
