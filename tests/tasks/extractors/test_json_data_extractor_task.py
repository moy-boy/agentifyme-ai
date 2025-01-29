# pylint: disable=redefined-outer-name, invalid-name

import os
from typing import Any, Dict, List

import pytest

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelType,
)
from agentifyme.tasks import JSONDataExtractorTask
from agentifyme.utilities.env import load_env_file


@pytest.fixture(scope="session", autouse=True)
def load_env():
    file_path = os.path.join(os.getcwd(), ".env.test")
    load_env_file(file_path)


@pytest.fixture
def json_extractor_task():
    file_path = os.path.join(os.getcwd(), ".env.test")
    load_env_file(file_path)

    api_key = os.getenv("OPENAI_API_KEY", "")
    language_model_config = LanguageModelConfig(
        model=LanguageModelType.OPENAI_GPT4o_MINI,
        api_key=api_key,
        json_mode=True,
    )

    return JSONDataExtractorTask(language_model_config=language_model_config)


def test_json_data_extractor_simple(
    json_extractor_task: JSONDataExtractorTask,
):
    text = "John Doe can be reached at johndoe@example.com or at 123-456-7890."
    output_schema = "Extract the name, email, and phone as a valid JSON object."
    json_data = json_extractor_task(text=text, output_schema=output_schema)

    assert json_data is not None
    assert "name" in json_data
    assert "email" in json_data
    assert "phone" in json_data

    # Validate the extracted data
    assert json_data["name"] == "John Doe"
    assert json_data["email"] == "johndoe@example.com"
    assert json_data["phone"] == "123-456-7890"


def test_json_data_extractor_nested_simple(
    json_extractor_task: JSONDataExtractorTask,
):
    text = "The movie 'Inception' directed by Christopher Nolan stars Leonardo DiCaprio, Joseph Gordon-Levitt, and Ellen Page."
    output_schema = "Extract the movie title, director, and main cast members as a valid JSON object. The main cast members should be a list of strings."
    json_data = json_extractor_task(text=text, output_schema=output_schema)

    assert json_data is not None

    # Validate 'title' key and its value
    assert "title" in json_data
    assert json_data["title"] == "Inception"

    # Validate 'director' key and its value
    assert "director" in json_data
    assert json_data["director"] == "Christopher Nolan"

    # Validate the existence of a key containing "cast" and its type
    cast_key = None
    for key in json_data:
        if "cast" in key:
            cast_key = key
            break

    assert cast_key is not None, "No key containing 'cast' found"
    assert isinstance(json_data[cast_key], list)
    assert "Leonardo DiCaprio" in json_data[cast_key]


def test_json_data_extractor_with_str_schema(
    json_extractor_task: JSONDataExtractorTask,
):
    text = """Order #12345 placed on July 28, 2024, includes a 'Sony WH-1000XM4 Headphones'
      for $299 and a 'Dell XPS 13 Laptop' for $999. The total amount is $1298,
      shipped to 123 Main St, Springfield."""

    output_schema = """
        Extract order number, order date, items with their names and prices, total amount,
        and shipping address as valid JSON object in the following JSON format.

        {
            "order_number": "67890",
            "order_date": "2024-08-05",
            "items": [
                {
                "name": "Apple AirPods Pro",
                "price": "$249"
                },
                {
                "name": "MacBook Pro 14-inch",
                "price": "$1999"
                }
            ],
            "total_amount": "$2248",
            "shipping_address": "456 Elm St, Metropolis"
        }
    """

    data = json_extractor_task(text=text, output_schema=output_schema)

    assert data is not None

    # Asserting top-level keys and their values
    assert data["order_number"] == "12345"
    assert data["order_date"] == "2024-07-28"
    assert data["total_amount"] == "$1298"
    assert data["shipping_address"] == "123 Main St, Springfield"

    # Asserting the items list
    assert len(data["items"]) == 2

    # Asserting the first item details
    assert data["items"][0]["name"] == "Sony WH-1000XM4 Headphones"
    assert data["items"][0]["price"] == "$299"

    # Asserting the second item details
    assert data["items"][1]["name"] == "Dell XPS 13 Laptop"
    assert data["items"][1]["price"] == "$999"


def test_extract_json(json_extractor_task: JSONDataExtractorTask):
    test_cases: List[Dict[str, Any]] = [
        # Test case 1: Well-formed JSON
        {
            "input": '{"key": "value"}',
            "expected": {"key": "value"},
            "description": "Simple well-formed JSON",
        },
        # Test case 2: Text with embedded JSON
        {
            "input": 'Some text {"key": "value"} some more text',
            "expected": {"key": "value"},
            "description": "Text with embedded JSON",
        },
        # Test case 3: Multiple JSON objects in text
        {
            "input": '{"key1": "value1"} and {"key2": "value2"}',
            "expected": {"key1": "value1"},
            "description": "Multiple JSON objects in text",
        },
        # Test case 4: Invalid JSON
        {
            "input": 'Some text {key: "value"}',
            "expected": None,
            "description": "Invalid JSON",
        },
        # Test case 5: No JSON in text
        {
            "input": "Just some plain text.",
            "expected": None,
            "description": "No JSON in text",
        },
        # Test case 6: Text with JSON in code block
        {
            "input": 'Some text ```json{"key": "value"}``` some more text',
            "expected": {"key": "value"},
            "description": "Text with JSON in code block",
        },
    ]

    for i, case in enumerate(test_cases):
        result = json_extractor_task.extract_json(case["input"])
        assert result == case["expected"], f"Test case {i + 1} failed: {case['description']}"
        print(f"Test case {i + 1} passed: {case['description']}")


@pytest.mark.asyncio
async def test_json_data_extractor_simple_async(
    json_extractor_task: JSONDataExtractorTask,
):
    text = "John Doe can be reached at johndoe@example.com or at 123-456-7890."
    output_schema = "Extract the name, email, and phone as a valid JSON object."
    json_data = await json_extractor_task.arun(text=text, output_schema=output_schema)

    assert json_data is not None
    assert "name" in json_data
    assert "email" in json_data
    assert "phone" in json_data

    # Validate the extracted data
    assert json_data["name"] == "John Doe"
    assert json_data["email"] == "johndoe@example.com"
    assert json_data["phone"] == "123-456-7890"


@pytest.mark.asyncio
async def test_json_data_extractor_nested_simple_async(
    json_extractor_task: JSONDataExtractorTask,
):
    text = "The movie 'Inception' directed by Christopher Nolan stars Leonardo DiCaprio, Joseph Gordon-Levitt, and Ellen Page."
    output_schema = "Extract the movie title, director, and main cast members as a valid JSON object. The main cast members should be a list of strings."
    json_data = await json_extractor_task.arun(text=text, output_schema=output_schema)

    assert json_data is not None

    # Validate 'title' key and its value
    assert "title" in json_data
    assert json_data["title"] == "Inception"

    # Validate 'director' key and its value
    assert "director" in json_data
    assert json_data["director"] == "Christopher Nolan"

    # Validate the existence of a key containing "cast" and its type
    cast_key = next((key for key in json_data if "cast" in key), None)
    assert cast_key is not None, "No key containing 'cast' found"
    assert isinstance(json_data[cast_key], list)
    assert "Leonardo DiCaprio" in json_data[cast_key]


@pytest.mark.asyncio
async def test_json_data_extractor_with_str_schema_async(
    json_extractor_task: JSONDataExtractorTask,
):
    text = """Order #12345 placed on July 28, 2024, includes a 'Sony WH-1000XM4 Headphones'
      for $299 and a 'Dell XPS 13 Laptop' for $999. The total amount is $1298,
      shipped to 123 Main St, Springfield."""

    output_schema = """
        Extract order number, order date, items with their names and prices, total amount,
        and shipping address as valid JSON object in the following JSON format.

        {
            "order_number": "67890",
            "order_date": "2024-08-05",
            "items": [
                {
                "name": "Apple AirPods Pro",
                "price": "$249"
                },
                {
                "name": "MacBook Pro 14-inch",
                "price": "$1999"
                }
            ],
            "total_amount": "$2248",
            "shipping_address": "456 Elm St, Metropolis"
        }
    """

    data = await json_extractor_task.arun(text=text, output_schema=output_schema)
    assert isinstance(data, dict)
    assert data is not None

    # Asserting top-level keys and their values
    assert "order_number" in data
    assert data.get("order_number") == "12345"
    assert "order_date" in data
    assert data.get("order_date") == "2024-07-28"
    assert "total_amount" in data
    assert data.get("total_amount") == "$1298"
    assert "shipping_address" in data
    assert data.get("shipping_address") == "123 Main St, Springfield"

    # Asserting the items list
    assert "items" in data
    items = data.get("items", [])
    assert len(items) == 2

    # Asserting the first item details
    assert "name" in items[0]
    assert items[0].get("name") == "Sony WH-1000XM4 Headphones"
    assert "price" in items[0]
    assert items[0].get("price") == "$299"

    # Asserting the second item details
    assert "name" in items[1]
    assert items[1].get("name") == "Dell XPS 13 Laptop"
    assert "price" in items[1]
    assert items[1].get("price") == "$999"


@pytest.mark.asyncio
async def test_extract_json_async(json_extractor_task: JSONDataExtractorTask):
    test_cases: List[Dict[str, Any]] = [
        # Test case 1: Well-formed JSON
        {
            "input": '{"key": "value"}',
            "expected": {"key": "value"},
            "description": "Simple well-formed JSON",
        },
        # Test case 2: Text with embedded JSON
        {
            "input": 'Some text {"key": "value"} some more text',
            "expected": {"key": "value"},
            "description": "Text with embedded JSON",
        },
        # Test case 3: Multiple JSON objects in text
        {
            "input": '{"key1": "value1"} and {"key2": "value2"}',
            "expected": {"key1": "value1"},
            "description": "Multiple JSON objects in text",
        },
        # Test case 4: Invalid JSON
        {
            "input": 'Some text {key: "value"}',
            "expected": None,
            "description": "Invalid JSON",
        },
        # Test case 5: No JSON in text
        {
            "input": "Just some plain text.",
            "expected": None,
            "description": "No JSON in text",
        },
        # Test case 6: Text with JSON in code block
        {
            "input": 'Some text ```json{"key": "value"}``` some more text',
            "expected": {"key": "value"},
            "description": "Text with JSON in code block",
        },
    ]

    for i, case in enumerate(test_cases):
        result = json_extractor_task.extract_json(case["input"])
        assert result == case["expected"], f"Test case {i + 1} failed: {case['description']}"
        print(f"Test case {i + 1} passed: {case['description']}")
