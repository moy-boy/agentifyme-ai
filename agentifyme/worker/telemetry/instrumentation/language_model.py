import copy
from collections.abc import Callable, Collection
from importlib import import_module
from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from wrapt import wrap_function_wrapper

from agentifyme.ml.llm import (
    LanguageModel,
    LanguageModelConfig,
    LanguageModelResponse,
    LanguageModelType,
    Message,
    OpenAILanguageModel,
    Role,
    get_language_model,
)
from agentifyme.worker.callback import CallbackHandler

__LLM_MODULE__ = "agentifyme.ml.llm"


class LanguageModelInstrumentor(BaseInstrumentor):
    __slots__ = [
        "_openai_agenerate",
        "_openai_agenerate_stream",
        "_openai_generate",
        "_openai_generate_stream",
    ]

    def __init__(self, callback_handler: CallbackHandler):
        super().__init__()
        self._callback_handler = callback_handler

    def instrumentation_dependencies(self) -> Collection[str]:
        return []

    def _instrument(self, **kwargs: Any):
        self._openai_generate = OpenAILanguageModel.generate
        self._openai_agenerate = OpenAILanguageModel.agenerate
        self._openai_generate_stream = OpenAILanguageModel.generate_stream

        llm_module = import_module(__LLM_MODULE__)
        wrap_function_wrapper(llm_module, "OpenAILanguageModel.generate", self._instrument_generate)
        wrap_function_wrapper(llm_module, "OpenAILanguageModel.agenerate", self._instrument_agenerate)

    def _uninstrument(self, **kwargs: Any):
        OpenAILanguageModel.generate = self._openai_generate
        OpenAILanguageModel.agenerate = self._openai_agenerate
        OpenAILanguageModel.generate_stream = self._openai_generate_stream

    def _instrument_generate(self, wrapped: Callable[..., Any], instance: LanguageModel, args: tuple[type, Any], kwargs: dict[str, Any]) -> LanguageModelResponse:
        provider, _ = instance.get_model_name(instance.llm_model)
        result = wrapped(*args, **kwargs)
        return result

    async def _instrument_agenerate(self, wrapped, instance: LanguageModel, args: tuple[type, Any], kwargs: dict[str, Any]) -> LanguageModelResponse:
        _kwargs = copy.deepcopy(kwargs)
        _kwargs.update(zip(wrapped.__code__.co_varnames, args, strict=False))
        provider, _ = instance.get_model_name(instance.llm_model)
        result = await wrapped(*args, **kwargs)
        return result
