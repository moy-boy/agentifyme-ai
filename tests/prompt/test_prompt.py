import os

import pytest

from agentifyme.prompt import PromptTemplate


@pytest.fixture
def yaml_path(request):
    # Get the filename from the parameter
    filename = request.param
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "prompt", filename)
    return file_path


@pytest.mark.parametrize("yaml_path", ["basic_prompt.yaml"], indirect=True)
def test_basic_prompt(yaml_path):
    prompt_file_path = yaml_path
    assert os.path.exists(prompt_file_path)

    prompt_template = PromptTemplate.from_file(prompt_file_path)
    assert prompt_template is not None

    prompt = prompt_template.render_as_prompt(persona="personal assistant", question="How are you?")

    assert prompt is not None
    assert prompt.name == "Basic Prompt"
    assert prompt.description == "A basic prompt designed to ask a single question and provide a specific answer."
    expected_system_message = "You are a personal assistant. Please provide clear and concise answers to the user's queries without additional explanations."
    expected_content = "How are you?"

    assert prompt.system_message == expected_system_message
    assert prompt.content == expected_content


@pytest.mark.parametrize("yaml_path", ["topic_specific_prompt.yaml"], indirect=True)
def test_topic_specific_prompt(yaml_path):
    prompt_file_path = yaml_path
    assert os.path.exists(prompt_file_path)

    prompt_template = PromptTemplate.from_file(prompt_file_path)
    assert prompt_template is not None

    # Test case with weather topic
    prompt = prompt_template.render_as_prompt(
        persona="weather specialist",
        role="providing weather updates",
        tone="friendly",
        topic="weather",
        location="New York",
    )

    assert prompt is not None
    assert prompt.name == "Topic-Specific Question Prompt"
    assert prompt.description == "A prompt template designed to generate questions based on a specific topic."
    assert prompt.version == "1.0"
    assert prompt.tags is not None
    # assert "topic-specific" in prompt.tags
    # assert "question" in prompt.tags

    expected_system_message = (
        "You are a weather specialist assistant. Your primary role is to assist with providing weather updates tasks.\n"
        "Please ask clear and relevant questions based on the provided context. Maintain a friendly tone."
    )
    expected_content = "What is the current weather condition and temperature in New York?"

    assert prompt.system_message == expected_system_message
    assert prompt.content == expected_content

    # Test case with news topic
    prompt = prompt_template.render_as_prompt(persona="news anchor", role="providing news", tone="serious", topic="news")

    expected_system_message = (
        "You are a news anchor assistant. Your primary role is to assist with providing news tasks.\n"
        "Please ask clear and relevant questions based on the provided context. Maintain a serious tone."
    )
    expected_content = "What are today's top headlines?"

    assert prompt.system_message == expected_system_message
    assert prompt.content == expected_content

    # Test case with unknown topic
    prompt = prompt_template.render_as_prompt(
        persona="general assistant",
        role="answering various queries",
        tone="neutral",
        topic="unknown",
    )

    expected_system_message = (
        "You are a general assistant assistant. Your primary role is to assist with answering various queries tasks.\n"
        "Please ask clear and relevant questions based on the provided context. Maintain a neutral tone."
    )
    expected_content = "Could you provide more information about unknown?"

    assert prompt.system_message == expected_system_message
    assert prompt.content == expected_content


@pytest.mark.parametrize("yaml_path", ["multi_topic_prompt.yaml"], indirect=True)
def test_multi_topic_prompt(yaml_path):
    prompt_file_path = yaml_path
    assert os.path.exists(prompt_file_path)

    prompt_template = PromptTemplate.from_file(prompt_file_path)
    assert prompt_template is not None

    # Test case with multiple topics
    prompt = prompt_template.render_as_prompt(
        persona="advisor",
        role="providing guidance",
        tone="inquisitive",
        detail_level="detailed",
        topics=["time management", "key priorities", "effective communication"],
    )

    assert prompt is not None
    assert prompt.name == "Multi-Topic Question Prompt"
    assert prompt.description == "A prompt template designed to generate questions based on multiple topics of interest."
    assert prompt.version == "1.0"
    assert prompt.tags is not None
    # assert "multi-topic" in prompt.tags
    # assert "question" in prompt.tags

    expected_system_message = "As a advisor, your task is to providing guidance.\n" "Please generate questions that are inquisitive and provide detailed detail."
    expected_content = (
        "Here are some questions based on your interests:\n"
        "- What can you tell me about time management?\n"
        "- What can you tell me about key priorities?\n"
        "- What can you tell me about effective communication?"
    )

    assert prompt.system_message == expected_system_message
    assert prompt.content == expected_content

    # Test case with no specific topics
    prompt = prompt_template.render_as_prompt(
        persona="coach",
        role="mentoring",
        tone="curious",
        detail_level="general",
        topics=[],
    )

    expected_system_message = "As a coach, your task is to mentoring.\n" "Please generate questions that are curious and provide general detail."
    expected_content = "Can you provide more details about the topics you are interested in?"

    assert prompt.system_message == expected_system_message
    assert prompt.content == expected_content
