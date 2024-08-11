# pylint: disable=missing-function-docstring

from pydantic import BaseModel

from agentifyme.tasks import Task, TaskConfig, task


def test_simple_task():
    TaskConfig.reset_registry()

    @task
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    assert say_hello("world") == "Hello, world!"

    task_instance = TaskConfig.get("say_hello")
    assert task_instance is not None
    assert task_instance("world") == "Hello, world!"


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
        return QuoteResponse(
            quote="Hello, world!", author="AgentifyMe", icons=["🚀", "🤖"]
        )

    question = QuoteRequest(question="What is the meaning of life?")
    response = get_quote(question=question)

    assert get_quote(
        QuoteRequest(question="What is the meaning of life?")
    ) == QuoteResponse(quote="Hello, world!", author="AgentifyMe", icons=["🚀", "🤖"])


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
