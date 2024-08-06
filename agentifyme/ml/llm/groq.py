import os
from typing import Any, Dict, Iterator, List, Optional, Union

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
    from groq import Groq
    from groq.types.chat import (
        ChatCompletion,
        ChatCompletionAssistantMessageParam,
        ChatCompletionMessage,
        ChatCompletionMessageParam,
        ChatCompletionSystemMessageParam,
        ChatCompletionUserMessageParam,
    )

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqError(Exception):
    """Custom exception for Groq-specific errors."""

    pass


class GroqLanguageModel(LanguageModel):
    def __init__(
        self,
        llm_model: LanguageModelType,
        api_key: Optional[str] = None,
        llm_cache_type: CacheType = CacheType.NONE,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not GROQ_AVAILABLE:
            raise ImportError(
                "Groq library is not installed. Please install it to use GroqLanguageModel."
            )

        super().__init__(
            llm_model, llm_cache_type, system_prompt=system_prompt, **kwargs
        )

        _api_key = os.getenv("GROQ_API_KEY") if api_key is None else api_key
        if not _api_key:
            raise ValueError("Groq API key is required")

        self.api_key = _api_key
        self.client = Groq(api_key=_api_key)
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
            raise NotImplementedError("Groq does not support function calling yet.")

        llm_messages = self._prepare_messages(messages)
        provider, model_name = self.get_model_name(self.model)

        assert provider == LanguageModelProvider.GROQ, f"Invalid provider: {provider}"

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=llm_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs,
            )

            usage = None
            if response.usage:
                cost = self.calculate_cost(
                    model_name,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    cost=cost,
                    calls=1,
                )

            llm_response = LanguageModelResponse(
                message=response.choices[0].message.content,
                role=Role.ASSISTANT,
                tool_calls=None,
                usage=usage,
                cached=False,
                error=None,
            )

            return llm_response

        except Exception as e:
            return LanguageModelResponse(
                message=None,
                cached=False,
                error=f"Groq API call failed: {str(e)}",
            )

    def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolCall]] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs: Any,
    ) -> Iterator[LanguageModelResponse]:
        if tools:
            raise NotImplementedError("Groq does not support function calling yet.")

        llm_messages = self._prepare_messages(messages)
        provider, model_name = self.get_model_name(self.model)
        assert provider == LanguageModelProvider.GROQ, f"Invalid provider: {provider}"

        try:
            stream = self.client.chat.completions.create(
                model=model_name,
                messages=llm_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True,
                **kwargs,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield LanguageModelResponse(
                        message=chunk.choices[0].delta.content,
                        role=Role.ASSISTANT,
                        tool_calls=None,
                        usage=None,
                        cached=False,
                        error=None,
                    )
        except Exception as e:
            yield LanguageModelResponse(
                message=None,
                cached=False,
                error=f"Groq API Error: {str(e)}",
            )

    def _prepare_messages(
        self, messages: List[Message]
    ) -> List[ChatCompletionMessageParam]:
        llm_messages: List[ChatCompletionMessageParam] = []

        for message in messages:
            if message.content is None:
                continue

            if message.role == Role.SYSTEM:
                system_message = ChatCompletionSystemMessageParam(
                    content=message.content, role="system"
                )
                llm_messages.append(system_message)
            elif message.role == Role.USER:
                user_message = ChatCompletionUserMessageParam(
                    content=message.content, role="user"
                )
                llm_messages.append(user_message)
            elif message.role == Role.ASSISTANT:
                assistant_message = ChatCompletionAssistantMessageParam(
                    content=message.content, role="assistant"
                )
                llm_messages.append(assistant_message)
            else:
                raise ValueError(f"Invalid role: {message.role}")
        return llm_messages

    def calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        # Implement pricing logic based on Groq's pricing structure
        # This is a placeholder and should be updated with accurate pricing
        return 0.0  # Placeholder


# This function can be used to check if Groq is available
def is_groq_available():
    return GROQ_AVAILABLE
