# pylint: disable=missing-function-docstring
import datetime

import wrapt

from agentifyme import task, workflow
from agentifyme.components.task import TaskConfig
from agentifyme.components.workflow import WorkflowConfig


class CustomProxy(wrapt.ObjectProxy):
    def __enter__(self):
        print("CustomProxy: Entering context", self.__wrapped__.__class__)
        return self.__wrapped__.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        print("CustomProxy: Exiting context", self.__wrapped__.__class__)
        return self.__wrapped__.__exit__(exc_type, exc_value, traceback)

    def __call__(self, *args, **kwargs):
        print("CustomProxy: Calling", self.__wrapped__.__class__)
        return self.__wrapped__(*args, **kwargs)


def test_workflow_context():
    WorkflowConfig.reset_registry()

    @task
    def get_date() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @task
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    @workflow
    def greet(name: str) -> str:
        greeting = say_hello(name)
        today = get_date()

        return f"{greeting}!! Today is {today}."

    # Inject telemetry
    task_registry = TaskConfig._registry.copy()
    for task_name in TaskConfig._registry.keys():
        _task = TaskConfig._registry[task_name]
        _task.config.func = CustomProxy(_task.config.func)
        # _task = CustomProxy(_task)
        task_registry[task_name] = _task
    TaskConfig._registry = task_registry

    workflow_registry = WorkflowConfig._registry.copy()
    for workflow_name in WorkflowConfig._registry.keys():
        _workflow = WorkflowConfig._registry[workflow_name]
        print(_workflow)
        _workflow = CustomProxy(_workflow)
        workflow_registry[workflow_name] = workflow
    WorkflowConfig._registry = workflow_registry

    print(greet("world"))
    # assert greet("world") == "Hello, world!"
    # assert greet("agentifyme") == "Hello, agentifyme!"
    # assert greet("python") == "Hello, python!"

    # workflow_instance = WorkflowConfig.get("greet")
    # assert workflow_instance is not None
    # assert workflow_instance("world") == "Hello, world!"
    # assert workflow_instance("agentifyme") == "Hello, agentifyme!"
    # assert workflow_instance("python") == "Hello, python!"

    # workflow_config = workflow_instance.config
    # assert workflow_config is not None
    # assert workflow_config.name == "greet"
    # assert workflow_config.description == ""
