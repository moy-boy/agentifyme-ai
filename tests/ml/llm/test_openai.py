import os
from typing import List

import pytest

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelResponse,
    LanguageModelType,
    ToolCall,
    get_language_model,
)
from agentifyme.utilities.env import load_env_file


@pytest.fixture(scope="session", autouse=True)
def load_env():
    file_path = os.path.join(os.getcwd(), ".env.test")
    load_env_file(file_path)


@pytest.fixture(scope="session", autouse=True)
def openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "")


@pytest.fixture
def openai_language_model_gpt4o(openai_api_key: str) -> LanguageModelConfig:
    model = LanguageModelType.OPENAI_GPT4o
    config = LanguageModelConfig(model=model, api_key=openai_api_key)
    return config


def test_openai_language_model(
    openai_language_model_gpt4o: LanguageModelConfig,
):
    language_model = get_language_model(openai_language_model_gpt4o)

    prompt = "What is the capital of France?"
    response = language_model.generate_from_prompt(prompt)

    response_text = response.message

    assert response_text is not None
    assert response_text != ""
    assert "paris" in response_text.lower()


def test_openai_language_model_streaming(
    openai_language_model_gpt4o: LanguageModelConfig,
):
    language_model = get_language_model(openai_language_model_gpt4o)

    prompt = "Count from 1 to 5 slowly."
    responses: List[LanguageModelResponse] = []

    for chunk in language_model.generate_stream_from_prompt(prompt):
        assert isinstance(chunk, LanguageModelResponse)
        responses.append(chunk)

    assert len(responses) > 1  # Ensure we received multiple chunks
    full_response = "".join(r.message for r in responses if r.message)
    assert "1" in full_response and "5" in full_response


def test_openai_language_model_function_calling(
    openai_language_model_gpt4o: LanguageModelConfig,
):
    language_model = get_language_model(openai_language_model_gpt4o)

    get_weather_function = ToolCall(
        name="get_weather",
        description="Get the current weather in a given location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    )

    tools = [get_weather_function]

    prompt = "What's the weather like in London?"
    response = language_model.generate_from_prompt(prompt, tools=tools)

    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1

    if response.tool_calls is not None:
        for tool_call in response.tool_calls:
            assert tool_call.name == "get_weather"

            arguments = tool_call.arguments
            assert arguments is not None
            assert arguments.get("location") == "London"


def test_openai_language_model_temperature(
    openai_language_model_gpt4o: LanguageModelConfig,
):
    language_model = get_language_model(openai_language_model_gpt4o)
    prompt = "Generate a random adjective:"

    # Low temperature (more deterministic)
    response_low_temp = language_model.generate_from_prompt(prompt=prompt, temperature=0.1)

    # High temperature (more random)
    response_high_temp = language_model.generate_from_prompt(prompt, temperature=0.9)

    assert response_low_temp.message != response_high_temp.message


def test_openai_language_model_max_tokens(
    openai_language_model_gpt4o: LanguageModelConfig,
):
    language_model = get_language_model(openai_language_model_gpt4o)
    prompt = "Write a long paragraph about artificial intelligence."

    response_short = language_model.generate_from_prompt(prompt, max_tokens=20)
    response_long = language_model.generate_from_prompt(prompt, max_tokens=100)

    assert response_short.message is not None
    assert response_long.message is not None
    assert len(response_short.message.split()) < len(response_long.message.split())


def test_openai_language_model_error_handling(
    openai_language_model_gpt4o: LanguageModelConfig,
):
    # Intentionally use an invalid API key
    invalid_config = LanguageModelConfig(model=LanguageModelType.OPENAI_GPT4o, api_key="invalid_key")
    language_model = get_language_model(invalid_config)

    prompt = "This should fail due to invalid API key."

    with pytest.raises(ValueError) as excinfo:
        language_model.generate_from_prompt(prompt)

    assert "OpenAI API call failed" in str(excinfo.value)
