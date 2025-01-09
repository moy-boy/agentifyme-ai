import asyncio
from datetime import datetime
from typing import Any, Callable


class CallbackHandler:
    def __init__(self):
        self.callbacks = {}

    def register(self, event_type: str, callback: Callable) -> None:
        """Register a callback function for a specific event type."""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    def notify(self, event_type: str, data: Any = None) -> None:
        """Notify all callbacks registered for an event type."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                # if callback is a coroutine, await it
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)

    def on_exec_start(self, data: dict):
        data["event_type"] = "exec_start"
        self.notify("exec_start", data)

    def on_exec_end(self, data: dict):
        data["event_type"] = "exec_end"
        self.notify("exec_end", data)

    def on_task_start(self, data: dict):
        data["event_type"] = "task_start"
        self.notify("task_start", data)

    def on_task_end(self, data: dict):
        data["event_type"] = "task_end"
        self.notify("task_end", data)

    def on_workflow_scheduled(self, data: dict):
        data["event_type"] = "workflow_scheduled"
        self.notify("workflow_scheduled", data)

    def on_workflow_start(self, data: dict):
        data["event_type"] = "workflow_start"
        self.notify("workflow_start", data)

    def on_workflow_end(self, data: dict):
        data["event_type"] = "workflow_end"
        self.notify("workflow_end", data)

    def on_trigger_start(self, data: dict):
        data["event_type"] = "trigger_start"
        self.notify("trigger_start", data)

    def on_trigger_end(self, data: dict):
        data["event_type"] = "trigger_end"
        self.notify("trigger_end", data)

    def on_llm_start(self, data: dict):
        data["event_type"] = "llm_start"
        self.notify("llm_start", data)

    def on_llm_end(self, data: dict):
        data["event_type"] = "llm_end"
        self.notify("llm_end", data)

    def on_tool_start(self, data: dict):
        data["event_type"] = "tool_start"
        self.notify("tool_start", data)

    def on_tool_end(self, data: dict):
        data["event_type"] = "tool_end"
        self.notify("tool_end", data)
