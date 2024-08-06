# pylint: disable=missing-function-docstring

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
