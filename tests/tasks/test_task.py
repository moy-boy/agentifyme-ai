# pylint: disable=missing-function-docstring

import pytest
from pydantic import BaseModel

from agentifyme.components.task import TaskConfig, task


def test_simple_task():
    TaskConfig.reset_registry()

    @task
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    assert say_hello("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello")
    assert task_instance is not None
    assert task_instance("world") == "Hello, world!"


@pytest.mark.asyncio
async def test_simple_async_task():
    TaskConfig.reset_registry()

    @task
    async def say_hello_async(name: str) -> str:
        return f"Hello, {name}!"

    assert await say_hello_async("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello_async")
    assert task_instance is not None
    assert await task_instance("world") == "Hello, world!"


def test_task_registry_string_arguments():
    TaskConfig.reset_registry()

    @task
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    assert say_hello("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello")
    assert task_instance is not None
    assert task_instance("world") == "Hello, world!"

    for task_name, task_instance in TaskConfig._registry.items():
        print(task_name, task_instance)
        print(task_instance.config.model_dump_json(indent=2, exclude={"func"}))


@pytest.mark.asyncio
async def test_async_task_registry_string_arguments():
    TaskConfig.reset_registry()

    @task
    async def say_hello_async(name: str) -> str:
        return f"Hello, {name}!"

    assert await say_hello_async("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello_async")
    assert task_instance is not None
    assert await task_instance("world") == "Hello, world!"

    for task_name, task_instance in TaskConfig._registry.items():
        print(task_name, task_instance)
        print(task_instance.config.model_dump_json(indent=2, exclude={"func"}))


def test_task_registry_pydantic_arguments():
    TaskConfig.reset_registry()

    class QuoteRequest(BaseModel):
        question: str

    class QuoteResponse(BaseModel):
        quote: str
        author: str
        icons: list[str]

    @task
    def get_quote(question: QuoteRequest) -> QuoteResponse:
        return QuoteResponse(quote="Hello, world!", author="AgentifyMe", icons=["🚀", "🤖"])

    question = QuoteRequest(question="What is the meaning of life?")
    response = get_quote(question=question)

    assert get_quote(QuoteRequest(question="What is the meaning of life?")) == QuoteResponse(quote="Hello, world!", author="AgentifyMe", icons=["🚀", "🤖"])


@pytest.mark.asyncio
async def test_async_task_registry_pydantic_arguments():
    TaskConfig.reset_registry()

    class QuoteRequest(BaseModel):
        question: str

    class QuoteResponse(BaseModel):
        quote: str
        author: str
        icons: list[str]

    @task
    async def get_quote_async(question: QuoteRequest) -> QuoteResponse:
        return QuoteResponse(quote="Hello, world!", author="AgentifyMe", icons=["🚀", "🤖"])

    question = QuoteRequest(question="What is the meaning of life?")
    response = await get_quote_async(question=question)

    assert await get_quote_async(QuoteRequest(question="What is the meaning of life?")) == QuoteResponse(quote="Hello, world!", author="AgentifyMe", icons=["🚀", "🤖"])


def test_task_with_name_and_description():
    TaskConfig.reset_registry()

    @task(name="say_hello", description="Generate a greeting message.")
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    assert say_hello("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello")
    assert task_instance is not None
    assert task_instance("world") == "Hello, world!"

    task_config = task_instance.config
    assert task_config is not None
    assert task_config.name == "say_hello"
    assert task_config.description == "Generate a greeting message."


@pytest.mark.asyncio
async def test_async_task_with_name_and_description():
    TaskConfig.reset_registry()

    @task(name="say_hello_async", description="Generate an async greeting message.")
    async def say_hello_async(name: str) -> str:
        return f"Hello, {name}!"

    assert await say_hello_async("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello_async")
    assert task_instance is not None
    assert await task_instance("world") == "Hello, world!"

    task_config = task_instance.config
    assert task_config is not None
    assert task_config.name == "say_hello_async"
    assert task_config.description == "Generate an async greeting message."


@pytest.mark.asyncio
async def test_mix_sync_and_async_tasks():
    TaskConfig.reset_registry()

    @task
    def sync_task(x: int) -> int:
        return x * 2

    @task
    async def async_task(x: int) -> int:
        return x * 3

    assert sync_task(5) == 10
    assert await async_task(5) == 15

    sync_instance = TaskConfig.get("sync_task")
    async_instance = TaskConfig.get("async_task")

    assert sync_instance(7) == 14
    assert await async_instance(7) == 21
