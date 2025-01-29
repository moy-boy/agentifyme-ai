# pylint: disable=redefined-outer-name, invalid-name

import os
from datetime import date
from typing import List, Optional

import pytest
from pydantic import BaseModel

from agentifyme.ml.llm import (
    LanguageModelConfig,
    LanguageModelType,
)
from agentifyme.tasks import PydanticDataExtractorTask
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

    assert isinstance(output, WeatherData)
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

    output: Order = pydantic_extractor_task(input_data=text, output_type=Order)

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


# pylint: disable=redefined-outer-name, invalid-name


# Keep the existing fixtures


@pytest.mark.asyncio
async def test_pydantic_data_extractor_simple_async(
    pydantic_extractor_task: PydanticDataExtractorTask,
):
    class WeatherData(BaseModel):
        city: str
        temperature: float
        humidity: float

    text = "The weather in New York is 75 degrees Fahrenheit with 60% humidity."

    output = await pydantic_extractor_task.arun(input_data=text, output_type=WeatherData)

    assert isinstance(output, WeatherData)
    assert output is not None

    # validate the fields
    assert output.city == "New York"
    assert output.temperature == 75.0
    assert output.humidity == 60.0


@pytest.mark.asyncio
async def test_json_data_extractor_nested_async(
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

    output = await pydantic_extractor_task.arun(input_data=text, output_type=Order)
    assert isinstance(output, Order)

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


@pytest.mark.asyncio
async def test_pydantic_data_extractor_complex_async(
    pydantic_extractor_task: PydanticDataExtractorTask,
):
    class Author(BaseModel):
        name: str
        birth_year: int

    class Book(BaseModel):
        title: str
        author: Author
        publication_year: int
        genres: List[str]

    text = """
    "To Kill a Mockingbird" is a novel by Harper Lee, published in 1960.
    Lee was born in 1926 in Monroeville, Alabama. The book is considered
    a classic of modern American literature and is widely read in schools.
    It falls under the genres of Southern Gothic and Bildungsroman.
    """

    output = await pydantic_extractor_task.arun(input_data=text, output_type=Book)

    assert isinstance(output, Book)
    assert output is not None

    assert output.title == "To Kill a Mockingbird"
    assert output.publication_year == 1960
    assert output.author.name == "Harper Lee"
    assert output.author.birth_year == 1926
    assert output.genres == ["Southern Gothic", "Bildungsroman"]


@pytest.mark.asyncio
async def test_pydantic_data_extractor_with_missing_data_async(
    pydantic_extractor_task: PydanticDataExtractorTask,
):
    class MovieReview(BaseModel):
        title: str
        director: Optional[str] = None
        release_year: Optional[int] = None
        rating: float
        review: str

    text = """
    I watched "Inception" recently. It's a mind-bending thriller that keeps
    you guessing until the end. The special effects were incredible, and
    the plot was intricate and engaging. I'd give it a solid 4.5 out of 5.
    """

    output = await pydantic_extractor_task.arun(input_data=text, output_type=MovieReview)
    assert isinstance(output, MovieReview)

    assert output is not None

    assert output.title == "Inception"
    assert output.rating == 4.5
    assert len(output.review) > 0

    # These fields are not explicitly mentioned in the text, so they should be None
    assert output.director is None
    assert output.release_year is None
