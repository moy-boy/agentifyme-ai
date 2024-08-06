import re
from typing import Any, ClassVar, Dict

from pydantic import BaseModel


class AgentifyMeConfig(BaseModel):
    task_registry: ClassVar[Dict[str, "BaseModel"]] = {}
    workflow_registry: ClassVar[Dict[str, "BaseModel"]] = {}

    @classmethod
    def register_task(cls, task: "TaskConfig"):
        cls.task_registry[task.name] = task

    @classmethod
    def register_workflow(cls, workflow: "WorkflowConfig"):
        cls.workflow_registry[workflow.name] = workflow

    @classmethod
    def get_task(cls, task_name: str) -> "TaskConfig":
        return cls.task_registry.get(task_name)

    @classmethod
    def get_workflow(cls, workflow_name: str) -> "WorkflowConfig":
        return cls.workflow_registry.get(workflow_name)

    @classmethod
    def list_tasks(cls):
        print("Tasks:")
        for k, task in cls.task_registry.items():
            print(f"  - {k}: {task.description}")
        return cls.task_registry.keys()

    @classmethod
    def list_workflows(cls):
        print("Workflows:")
        for k, workflow in cls.workflow_registry.items():
            print(f"  - {k}: {workflow.description}")
        return cls.workflow_registry.keys()
