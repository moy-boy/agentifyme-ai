import os
from typing import Any, Dict, List, Optional

from agentifyme.ml.llm import LanguageModel

from .base import (
    CacheType,
    LanguageModel,
    LanguageModelProvider,
    LanguageModelResponse,
    LanguageModelType,
    Message,
    Role,
    TokenUsage,
    ToolCall,
)

try:
    import cohere

    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


class CohereError(Exception):
    """Custom exception for Cohere-specific errors."""

    pass


class CohereLanguageModel(LanguageModel):
    def __init__(
        self,
        llm_model: LanguageModelType,
        api_key: Optional[str] = None,
        llm_cache_type: CacheType = CacheType.NONE,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not COHERE_AVAILABLE:
            raise ImportError(
                "Cohere library is not installed. Please install it to use CohereLanguageModel."
            )

        super().__init__(
            llm_model, llm_cache_type, system_prompt=system_prompt, **kwargs
        )

        _api_key = os.getenv("COHERE_API_KEY") if api_key is None else api_key
        if not _api_key:
            raise ValueError("Cohere API key is required")

        self.api_key = _api_key
        self.client = cohere.Client(api_key=_api_key)
        self.model = llm_model

    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolCall]] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs,
    ) -> LanguageModelResponse:
        if tools:
            raise NotImplementedError("Cohere does not support function calling yet.")

        preamble = self.system_prompt or ""

        return LanguageModelResponse(
            message="",
            usage=TokenUsage(),
        )
