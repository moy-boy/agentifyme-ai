# pylint: disable=redefined-outer-name, invalid-name

import os
from datetime import date
from typing import List

import pytest
from pydantic import BaseModel

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelType,
)
from agentifyme.tasks.extractors import PydanticDataExtractorTask
from agentifyme.utilities.env import load_env_file


@pytest.fixture(scope="session", autouse=True)
def load_env():
    file_path = os.path.join(os.getcwd(), ".env.test")
    load_env_file(file_path)


@pytest.fixture
def pydantic_extractor_task() -> PydanticDataExtractorTask:
    file_path = os.path.join(os.getcwd(), ".env.test")
    load_env_file(file_path)

    api_key = os.getenv("OPENAI_API_KEY", "")
    language_model_config = LanguageModelConfig(
        model=LanguageModelType.OPENAI_GPT4o_MINI,
        api_key=api_key,
        json_mode=True,
    )

    return PydanticDataExtractorTask(language_model_config=language_model_config)


def test_pydantic_data_extractor_simple(
    pydantic_extractor_task: PydanticDataExtractorTask,
):
    class WeatherData(BaseModel):
        city: str
        temperature: float
        humidity: float

    text = "The weather in New York is 75 degrees Fahrenheit with 60% humidity."

    output = pydantic_extractor_task(input_data=text, output_type=WeatherData)

    assert output is not None

    # validate the fields
    assert output.city == "New York"
    assert output.temperature == 75.0
    assert output.humidity == 60.0


def test_json_data_extractor_nested(
    pydantic_extractor_task: PydanticDataExtractorTask,
):
    class Item(BaseModel):
        name: str
        price: str

    class Order(BaseModel):
        order_number: str
        order_date: date
        items: List[Item]
        total_amount: str
        shipping_address: str

    text = """Order #12345 placed on July 28, 2024, includes a 'Sony WH-1000XM4 Headphones'
      for $299 and a 'Dell XPS 13 Laptop' for $999. The total amount is $1298,
      shipped to 123 Main St, Springfield."""

    output = pydantic_extractor_task(input_data=text, output_type=Order)

    assert output is not None

    assert output.order_number == "12345"
    assert output.order_date == date(2024, 7, 28)
    assert output.total_amount == "$1298"
    assert output.shipping_address == "123 Main St, Springfield"

    assert len(output.items) == 2

    assert output.items[0].name == "Sony WH-1000XM4 Headphones"
    assert output.items[0].price == "$299"

    assert output.items[1].name == "Dell XPS 13 Laptop"
    assert output.items[1].price == "$999"
