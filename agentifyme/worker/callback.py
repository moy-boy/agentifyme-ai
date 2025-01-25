import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from loguru import logger


class EventType(Enum):
    TASK = "task"
    WORKFLOW = "workflow"
    LLM = "llm"
    TOOL = "tool"


class EventStage(Enum):
    INITIATED = "initiated"
    STARTED = "started"
    COMPLETED = "completed"
    FINISHED = "finished"
    PAUSED = "paused"
    RESUMED = "resumed"
    CANCELLED = "cancelled"


@dataclass
class Event:
    type: EventType
    stage: EventStage
    event_name: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.type.value, "event_stage": self.stage.value, "event_name": self.event_name, **self.data}


class CallbackHandler:
    def __init__(self):
        self.callbacks: dict[str, list[Callable]] = {}
        self.default_callbacks: list[Callable] = []  # New: List for default callbacks

    def register_default(self, callback: Callable) -> None:
        """Register a callback that will be called for all events"""
        self.default_callbacks.append(callback)

    def register(self, event_type: EventType | str, callback: Callable, event_stage: EventStage | str = None) -> None:
        """Register a callback function for specific event type and stage.
        If event_stage is None, callback will be registered for all stages of the event type.
        """
        if isinstance(event_type, str):
            event_type = EventType(event_type)
        if isinstance(event_stage, str) and event_stage:
            event_stage = EventStage(event_stage)

        # Create event key
        event_key = f"{event_type.value}"
        if event_stage:
            event_key = f"{event_key}.{event_stage.value}"

        if event_key not in self.callbacks:
            self.callbacks[event_key] = []
        self.callbacks[event_key].append(callback)

    async def _execute_callback(self, callback: Callable, data: Any):
        """Execute callback handling both async and sync callbacks"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Error executing callback: {e}", exc_info=True)

    async def notify(self, event: Event) -> None:
        """Notify all callbacks registered for an event.
        Handles both specific stage callbacks, general event type callbacks,
        and default callbacks.
        """
        event_dict = event.to_dict()
        tasks = []

        # Notify specific stage callbacks
        specific_key = f"{event.type.value}.{event.stage.value}"
        if specific_key in self.callbacks:
            for callback in self.callbacks[specific_key]:
                tasks.append(self._execute_callback(callback, event_dict))

        # Notify general event type callbacks
        general_key = f"{event.type.value}"
        if general_key in self.callbacks:
            for callback in self.callbacks[general_key]:
                tasks.append(self._execute_callback(callback, event_dict))

        # Notify default callbacks
        for callback in self.default_callbacks:
            tasks.append(self._execute_callback(callback, event_dict))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def fire_event(self, event_type: EventType | str, event_stage: EventStage | str, data: dict) -> None:
        """Fire an event synchronously.
        Creates and processes Event object with the given parameters.
        """
        event_name = f"{event_type}.{event_stage}"
        if isinstance(event_type, str):
            # Handle the "type.run" format
            if ".run" in event_type or ".execution" in event_type:
                event_type = event_type.split(".")[0]
            event_type = EventType(event_type)

        if isinstance(event_stage, str):
            event_stage = EventStage(event_stage)

        event = Event(type=event_type, stage=event_stage, event_name=event_name, data=data)

        # Create task for async notification
        asyncio.create_task(self.notify(event))

    async def fire_event_async(self, event_type: EventType | str, event_stage: EventStage | str, data: dict) -> None:
        """Fire an event asynchronously.
        Allows awaiting the completion of all callbacks.
        """
        event_name = f"{event_type}.{event_stage}"
        if isinstance(event_type, str):
            if ".run" in event_type or ".execution" in event_type:
                event_type = event_type.split(".")[0]
            event_type = EventType(event_type)

        if isinstance(event_stage, str):
            event_stage = EventStage(event_stage)

        event = Event(type=event_type, stage=event_stage, event_name=event_name, data=data)

        await self.notify(event)
