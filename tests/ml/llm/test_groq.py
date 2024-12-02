import os
from typing import List

import pytest

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelResponse,
    LanguageModelType,
    get_language_model,
)
from agentifyme.utilities.env import load_env_file


@pytest.fixture(scope="session", autouse=True)
def load_env():
    file_path = os.path.join(os.getcwd(), ".env.test")
    load_env_file(file_path)


@pytest.fixture(scope="session", autouse=True)
def api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")


@pytest.fixture
def groq_language_model_llama_3_1_8b_instant(api_key: str) -> LanguageModelConfig:
    model = LanguageModelType.GROQ_LLAMA_3_1_8B_INSTANT
    config = LanguageModelConfig(model=model, api_key=api_key)
    return config


def test_groq_language_model(
    groq_language_model_llama_3_1_8b_instant: LanguageModelConfig,
):
    language_model = get_language_model(groq_language_model_llama_3_1_8b_instant)

    prompt = "What is the capital of France?"
    response = language_model.generate_from_prompt(prompt)

    response_text = response.message

    assert response_text is not None
    assert response_text != ""
    assert "paris" in response_text.lower()


def test_groq_language_model_streaming(
    groq_language_model_llama_3_1_8b_instant: LanguageModelConfig,
):
    language_model = get_language_model(groq_language_model_llama_3_1_8b_instant)

    prompt = "Count from 1 to 5 slowly. Numerals only, please."
    responses: List[LanguageModelResponse] = []

    for chunk in language_model.generate_stream_from_prompt(prompt):
        assert isinstance(chunk, LanguageModelResponse)
        responses.append(chunk)

    assert len(responses) > 1  # Ensure we received multiple chunks
    full_response = "".join(r.message for r in responses if r.message)
    print(full_response)

    # Ensure the full response contains the numbers 1 to 5 in order
    assert "1" in full_response and "5" in full_response


# def test_groq_language_model_function_calling(
#     groq_language_model_llama_3_1_8b_instant: LanguageModelConfig,
# ):
#     language_model = get_language_model(groq_language_model_llama_3_1_8b_instant)

#     get_weather_function = ToolCall(
#         name="get_weather",
#         description="Get the current weather in a given location",
#         parameters={
#             "type": "object",
#             "properties": {
#                 "location": {
#                     "type": "string",
#                     "description": "The city and state, e.g. San Francisco, CA",
#                 },
#                 "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
#             },
#             "required": ["location"],
#         },
#     )

#     tools = [get_weather_function]

#     prompt = "What's the weather like in London?"
#     response = language_model.generate_from_prompt(prompt, tools=tools)

#     assert response.tool_calls is not None
#     assert len(response.tool_calls) == 1

#     if response.tool_calls is not None:
#         for tool_call in response.tool_calls:
#             assert tool_call.name == "get_weather"

#             arguments = tool_call.arguments
#             assert arguments is not None
#             assert arguments.get("location") == "London"


def test_groq_language_model_temperature(
    groq_language_model_llama_3_1_8b_instant: LanguageModelConfig,
):
    language_model = get_language_model(groq_language_model_llama_3_1_8b_instant)
    prompt = "Generate a random adjective:"

    # Low temperature (more deterministic)
    response_low_temp = language_model.generate_from_prompt(prompt=prompt, temperature=0.1)

    # High temperature (more random)
    response_high_temp = language_model.generate_from_prompt(prompt, temperature=0.9)

    assert response_low_temp.message != response_high_temp.message


def test_groq_language_model_max_tokens(
    groq_language_model_llama_3_1_8b_instant: LanguageModelConfig,
):
    language_model = get_language_model(groq_language_model_llama_3_1_8b_instant)
    prompt = "Write a long paragraph about artificial intelligence."

    response_short = language_model.generate_from_prompt(prompt, max_tokens=20)
    response_long = language_model.generate_from_prompt(prompt, max_tokens=100)

    assert response_short.message is not None
    assert response_long.message is not None
    assert len(response_short.message.split()) < len(response_long.message.split())


def test_groq_language_model_error_handling(
    groq_language_model_llama_3_1_8b_instant: LanguageModelConfig,
):
    # Intentionally use an invalid API key
    invalid_config = LanguageModelConfig(model=LanguageModelType.GROQ_LLAMA_3_1_8B_INSTANT, api_key="invalid_key")
    language_model = get_language_model(invalid_config)

    prompt = "This should fail due to invalid API key."

    response = language_model.generate_from_prompt(prompt)
    assert "Groq API call failed: Error code: 401" in str(response.error)
