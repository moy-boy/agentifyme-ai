import os

import pytest

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelType,
    get_language_model,
)
from agentifyme.utilities.env import load_env_file


@pytest.fixture(scope="session", autouse=True)
def api_key() -> str:
    if "ANTHROPIC_API_KEY" not in os.environ:
        file_path = os.path.join(os.getcwd(), ".env.test")
        load_env_file(file_path)

    return os.getenv("ANTHROPIC_API_KEY", "")


@pytest.fixture
def anthropic_language_model_claude_3_haiku(api_key: str) -> LanguageModelConfig:
    print("ANTHROPIC", api_key)
    model = LanguageModelType.ANTHROPIC_CLAUDE_3_HAIKU
    config = LanguageModelConfig(model=model, api_key=api_key)
    return config


def test_anthropic_language_model(
    anthropic_language_model_claude_3_haiku: LanguageModelConfig,
):
    language_model = get_language_model(anthropic_language_model_claude_3_haiku)

    prompt = "What is the capital of England?"
    response = language_model.generate_from_prompt(prompt)

    response_text = response.message

    assert response_text is not None
    assert response_text != ""
    assert "london" in response_text.lower()


def test_anthropic_language_model_temperature(
    anthropic_language_model_claude_3_haiku: LanguageModelConfig,
):
    language_model = get_language_model(anthropic_language_model_claude_3_haiku)
    prompt = "Generate a random adjective:"

    # Low temperature (more deterministic)
    response_low_temp = language_model.generate_from_prompt(prompt=prompt, temperature=0.1)

    # High temperature (more random)
    response_high_temp = language_model.generate_from_prompt(prompt, temperature=0.9)

    assert response_low_temp.message != response_high_temp.message


def test_anthropic_language_model_max_tokens(
    anthropic_language_model_claude_3_haiku: LanguageModelConfig,
):
    language_model = get_language_model(anthropic_language_model_claude_3_haiku)
    prompt = "Write a long paragraph about artificial intelligence."

    response_short = language_model.generate_from_prompt(prompt, max_tokens=20)
    response_long = language_model.generate_from_prompt(prompt, max_tokens=100)

    assert response_short.message is not None
    assert response_long.message is not None
    assert len(response_short.message.split()) < len(response_long.message.split())


def test_anthropic_language_model_error_handling(
    anthropic_language_model_claude_3_haiku: LanguageModelConfig,
):
    import anthropic

    # Intentionally use an invalid API key
    invalid_config = LanguageModelConfig(model=LanguageModelType.ANTHROPIC_CLAUDE_3_HAIKU, api_key="invalid_key")
    language_model = get_language_model(invalid_config)

    prompt = "This should fail due to invalid API key."

    with pytest.raises(anthropic.AuthenticationError) as excinfo:
        language_model.generate_from_prompt(prompt)

    assert "invalid x-api-key" in str(excinfo.value)
