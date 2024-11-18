import hashlib
import json
import os
from typing import Any, Dict, Iterable, Iterator, List, Literal, Optional, Tuple

from joblib import Memory
from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    NotGiven,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.shared_params.function_definition import FunctionDefinition

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


def llm_cache_key(model_name, llm_messages, tools):
    raw_key = model_name
    if len(llm_messages) > 0:
        raw_key = raw_key + str(llm_messages)

    if len(tools) > 0:
        raw_key = raw_key + str(tools)

    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return hashed_key


class LLMCacheJoblib(Memory):
    def _cache_key(self, func, *args, **kwargs):
        model_name, llm_messages, tools = args
        return llm_cache_key(model_name, llm_messages, tools)


class OpenAILanguageModelException:
    pass


class OpenAILanguageModel(LanguageModel):
    def __init__(
        self,
        llm_model: LanguageModelType,
        api_key: Optional[str] = None,
        llm_cache_type: CacheType = CacheType.NONE,
        system_prompt: Optional[str] = None,
        api_base_url: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            llm_model, llm_cache_type, system_prompt=system_prompt, **kwargs
        )

        _api_key = os.getenv("OPENAI_API_KEY") if api_key is None else api_key
        if not _api_key:
            raise ValueError("OpenAI API key is required")

        self.api_key = _api_key
        self.client = OpenAI(
            api_key=_api_key,
            base_url=api_base_url,
            organization=organization,
            project=project,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.async_client = AsyncOpenAI(
            api_key=_api_key,
            base_url=api_base_url,
            organization=organization,
            project=project,
            timeout=timeout,
            max_retries=max_retries,
        )

        self.model = llm_model
        self.json_mode = json_mode

        self.llm_cache: Optional[LLMCacheJoblib] = None

        if self.llm_cache_type == CacheType.DISK:
            self.llm_cache = LLMCacheJoblib(location="joblib_cache", verbose=0)
        elif self.llm_cache_type == CacheType.MEMORY:
            self.llm_cache = LLMCacheJoblib(location=None, verbose=0)

    def _to_openai_tools(
        self, tools: Optional[List[ToolCall]] = None
    ) -> Iterable[ChatCompletionToolParam] | NotGiven:
        if tools is None:
            return NotGiven()

        _tools = (
            [{"name": tool.name, "parameters": tool.parameters} for tool in tools]
            if tools
            else None
        )

        openai_tools: Iterable[ChatCompletionToolParam] | NotGiven = NotGiven()

        if _tools:
            _openai_tools: List[ChatCompletionToolParam] = []

            for tool in _tools:
                fn_parameters: Dict[str, object] = {}

                parameters = tool.get("parameters")

                if parameters is not None and isinstance(parameters, dict):
                    for k, v in parameters.items():
                        fn_parameters[k] = v

                openai_tool = FunctionDefinition(
                    name=str(tool["name"]),
                    description=str(tool.get("description", "")),
                    parameters=fn_parameters,
                )

                _openai_tools.append(
                    ChatCompletionToolParam(
                        type="function",
                        function=openai_tool,
                    )
                )

            openai_tools = _openai_tools

        return openai_tools

    def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolCall]] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs,
    ) -> LanguageModelResponse:
        llm_messages = self._prepare_messages(messages)
        provider, model_name = self.get_model_name(self.model)

        assert provider == LanguageModelProvider.OPENAI, f"Invalid provider: {provider}"

        openai_tools = self._to_openai_tools(tools)

        if self.llm_cache is not None:
            response = self.llm_cache.cache(self._call_openai)(
                model_name,
                llm_messages,
                openai_tools,
                max_tokens,
                temperature,
                **kwargs,
            )
        else:
            response = self._call_openai(
                model_name,
                llm_messages,
                openai_tools,
                max_tokens,
                temperature,
                **kwargs,
            )

        llm_response = self._process_response(response)

        return llm_response

    async def agenerate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolCall]] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs: Any,
    ) -> LanguageModelResponse:
        llm_messages = self._prepare_messages(messages)
        provider, model_name = self.get_model_name(self.model)
        assert provider == LanguageModelProvider.OPENAI, f"Invalid provider: {provider}"
        openai_tools = self._to_openai_tools(tools)

        # TODO: Add support for async cache
        response = await self._call_openai_async(
            model_name,
            llm_messages,
            openai_tools,
            max_tokens,
            temperature,
            **kwargs,
        )

        llm_response = self._process_response(response)
        return llm_response

    def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolCall]] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs: Any,
    ) -> Iterator[LanguageModelResponse]:
        llm_messages = self._prepare_messages(messages)
        provider, model_name = self.get_model_name(self.model)
        assert provider == LanguageModelProvider.OPENAI, f"Invalid provider: {provider}"

        openai_functions = self._to_openai_tools(tools)

        try:
            stream = self.client.chat.completions.create(
                model=model_name,
                messages=llm_messages,
                tools=openai_functions,
                max_tokens=max_tokens,
                temperature=temperature,
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
        except (APIError, RateLimitError, APIConnectionError) as e:
            yield LanguageModelResponse(
                message=None,
                cached=False,
                error=str(e),
            )
        except OpenAIError as e:
            # This catches any other OpenAI-specific errors
            yield LanguageModelResponse(
                message=None,
                cached=False,
                error=f"OpenAI Error: {str(e)}",
            )
        except Exception as e:
            # As a last resort, catch any other unexpected errors
            yield LanguageModelResponse(
                message=None,
                cached=False,
                error=f"Unexpected error: {str(e)}",
            )

    def _call_openai(
        self,
        model_name: str,
        llm_messages: List[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NotGiven(),
        max_tokens: int = 256,
        temperature: float = 0.5,
        **kwargs: Any,
    ) -> ChatCompletion:
        try:
            response_format: ResponseFormat = {
                "type": "json_object" if self.json_mode else "text"
            }
            response = self.client.chat.completions.create(
                model=model_name,
                messages=llm_messages,
                tools=tools,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
                **kwargs,
            )
            return response
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {str(e)}") from e

    async def _call_openai_async(
        self,
        model_name: str,
        llm_messages: List[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NotGiven(),
        max_tokens: int = 256,
        temperature: float = 0.5,
        **kwargs: Any,
    ) -> ChatCompletion:
        try:
            response_format: ResponseFormat = {
                "type": "json_object" if self.json_mode else "text"
            }
            response = await self.async_client.chat.completions.create(
                model=model_name,
                messages=llm_messages,
                tools=tools,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
                **kwargs,
            )
            return response
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {str(e)}") from e

    def _prepare_messages(
        self, messages: List[Message]
    ) -> List[ChatCompletionMessageParam]:
        llm_messages: List[ChatCompletionMessageParam] = []

        for message in messages:
            if message.content is None:
                continue

            if message.role == Role.USER:
                user_message = ChatCompletionUserMessageParam(
                    content=message.content, role="user"
                )
                llm_messages.append(user_message)
            elif message.role == Role.SYSTEM:
                system_message = ChatCompletionSystemMessageParam(
                    content=message.content, role="system"
                )
                llm_messages.append(system_message)
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
        # Implement pricing logic based on OpenAI's pricing structure
        # This is a simplified example and should be updated with accurate pricing
        if "gpt-3.5" in model:
            return (prompt_tokens * 0.0015 + completion_tokens * 0.002) / 1000
        elif "gpt-4" in model:
            return (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        else:
            return 0.0

    def _process_response(self, response: ChatCompletion) -> LanguageModelResponse:
        """Process the API response into a LanguageModelResponse"""
        usage = None
        if response.usage:
            cost = self.calculate_cost(
                self.model.value,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
            )
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                cost=cost,
                calls=1,
            )

        tool_calls: List[ToolCall] = []
        for choice in response.choices:
            if choice.message.tool_calls is not None:
                for t in choice.message.tool_calls:
                    _function = t.function
                    tool = ToolCall(
                        name=_function.name,
                        arguments=json.loads(_function.arguments),
                        tool_call_id=t.id,
                    )
                    tool_calls.append(tool)

        return LanguageModelResponse(
            message=response.choices[0].message.content,
            role=Role.ASSISTANT,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            cached=False,
            error=None,
        )
