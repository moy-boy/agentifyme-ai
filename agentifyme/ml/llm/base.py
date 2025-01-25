from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import Enum
from typing import Any

from openai import BaseModel

from agentifyme.cache import CacheType


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ToolCall(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    arguments: dict[str, Any] | None = None
    tool_call_id: str | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    calls: int = 0


class Message(BaseModel):
    role: Role
    content: str | None = None
    tools: list[ToolCall] | None = None


class LanguageModelResponse(BaseModel):
    """Class representing response from LLM.
    """

    message: str | None = None
    role: Role = Role.ASSISTANT
    tool_id: str = ""  # used by OpenAIAssistant
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage | None = None
    cached: bool = False
    error: str | None = None


class LLMResponseError(Exception):
    """Error raised when LLM response is invalid"""


class LanguageModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    GROQ = "groq"
    TOGETHER = "together"


class LanguageModelType(str, Enum):
    OPENAI_GPT3_5_TURBO = "openai/gpt3-5-turbo"
    OPENAI_GPT4 = "openai/gpt-4"
    OPENAI_GPT4_32K = "openai/gpt-4-32k"
    OPENAI_GPT4o = "openai/gpt-4o"
    OPENAI_GPT4o_MINI = "openai/gpt-4o-mini"
    OPENAI_TEXT_MODERATION = "openai/text-moderation-latest"

    # Cohere
    COHERE_COMMAND = "cohere/command"
    COHERE_COMMAND_R = "cohere/command-r"
    COHERE_COMMAND_R_PLUS = "cohere/command-r-plus"
    COHERE_COMMAND_LIGHT = "cohere/command-light"

    # Anthropic
    ANTHROPIC_CLAUDE_3_5_SONNET = "anthropic/claude-3-5-sonnet-20240620"
    ANTHROPIC_CLAUDE_3_OPUS = "anthropic/claude-3-opus-20240229"
    ANTHROPIC_CLAUDE_3_SONNET = "anthropic/claude-3-sonnet-20240229"
    ANTHROPIC_CLAUDE_3_HAIKU = "anthropic/claude-3-haiku-20240307"

    # Groq
    GROQ_LLAMA_3_1_405B_REASONING = "groq/llama-3.1-405b-reasoning"
    GROQ_LLAMA_3_1_70B_VERSATILE = "groq/llama-3.1-70b-versatile"
    GROQ_LLAMA_3_1_8B_INSTANT = "groq/llama-3.1-8b-instant"
    GROQ_LLAMA3_GROQ_70B_8192_TOOL_USE_PREVIEW = "groq/llama3-groq-70b-8192-tool-use-preview"
    GROQ_LLAMA3_GROQ_8B_8192_TOOL_USE_PREVIEW = "groq/llama3-groq-8b-8192-tool-use-preview"

    # Together
    TOGETHER_SERVERLESS_META_LLAMA_3_1_8B_INSTRUCT_TURBO = "together/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"


class LanguageModel(ABC):
    llm_model: LanguageModelType
    llm_cache_type: CacheType

    def __init__(
        self,
        llm_model: LanguageModelType,
        llm_cache_type: CacheType = CacheType.NONE,
        system_prompt: str | None = None,
        **kwargs: Any,
    ):
        self.llm_model = llm_model
        self.llm_cache_type = llm_cache_type
        self.system_prompt = system_prompt

    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        tools: list[ToolCall] | None = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs,
    ) -> LanguageModelResponse:
        pass

    @abstractmethod
    async def agenerate(
        self,
        messages: list[Message],
        tools: list[ToolCall] | None = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs,
    ) -> LanguageModelResponse:
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolCall] | None = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs,
    ) -> Iterator[LanguageModelResponse]:
        pass

    def generate_stream_from_prompt(
        self,
        prompt: str,
        system_prompt: str | None = None,
        tools: list[ToolCall] | None = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs,
    ) -> Iterator[LanguageModelResponse]:
        messages = []
        if system_prompt is not None:
            messages.append(
                Message(
                    role=Role.SYSTEM,
                    content=system_prompt,
                    tools=tools,
                ),
            )

        messages.append(
            Message(
                role=Role.USER,
                content=prompt,
                tools=tools,
            ),
        )
        return self.generate_stream(
            messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def generate_from_prompt(
        self,
        prompt: str,
        system_prompt: str | None = None,
        tools: list[ToolCall] | None = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
    ) -> LanguageModelResponse:
        messages = []
        if system_prompt is not None:
            messages.append(
                Message(
                    role=Role.SYSTEM,
                    content=system_prompt,
                    tools=None,
                ),
            )

        messages.append(
            Message(
                role=Role.USER,
                content=prompt,
                tools=None,
            ),
        )
        return self.generate(
            messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    async def generate_from_prompt_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        tools: list[ToolCall] | None = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
    ) -> LanguageModelResponse:
        messages = []
        if system_prompt is not None:
            messages.append(
                Message(
                    role=Role.SYSTEM,
                    content=system_prompt,
                    tools=None,
                ),
            )

        messages.append(
            Message(
                role=Role.USER,
                content=prompt,
                tools=None,
            ),
        )
        return await self.agenerate(
            messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def generate_from_messages(self, messages: list[Message]) -> LanguageModelResponse:
        return self.generate(messages, [])

    @staticmethod
    def get_model_name(model: LanguageModelType) -> tuple[LanguageModelProvider, str]:
        try:
            provider_name, *model_parts = model.value.split("/")
            provider = LanguageModelProvider(provider_name)
            model_name = "/".join(model_parts)  # Join the remaining parts back together
            return provider, model_name
        except ValueError:
            raise ValueError(f"Invalid model type format: {model}. Expected format: 'provider/model'")
        except KeyError:
            raise ValueError(f"Unsupported provider: {provider_name}")
