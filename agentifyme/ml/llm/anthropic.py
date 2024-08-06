import os
from typing import Any, Iterator, List, Optional, Union

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
    import anthropic
    from anthropic.types import (
        ContentBlock,
        ImageBlockParam,
        MessageParam,
        TextBlockParam,
        ToolResultBlockParam,
        ToolUseBlockParam,
    )

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicError(Exception):
    """Custom exception for Anthropic-specific errors."""

    pass


class AnthropicLanguageModel(LanguageModel):
    def __init__(
        self,
        llm_model: LanguageModelType,
        api_key: Optional[str] = None,
        llm_cache_type: CacheType = CacheType.NONE,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic library is not installed. Please install it to use AnthropicLanguageModel."
            )

        super().__init__(
            llm_model, llm_cache_type, system_prompt=system_prompt, **kwargs
        )

        _api_key = os.getenv("ANTHROPIC_API_KEY") if api_key is None else api_key
        if not _api_key:
            raise ValueError("Anthropic API key is required")

        self.api_key = _api_key
        self.client = anthropic.Anthropic(api_key=_api_key)
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
        provider, model_name = self.get_model_name(self.model)

        anthropic_messages = self.convert_messages_to_params(messages)

        response = self.client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            messages=anthropic_messages,
        )

        response_text = ""

        for block in response.content:
            if block.type == "tool_use":
                # pass and do nothing for now:
                print(block)
                continue
            elif block.type == "text":
                response_text = block.text
            else:
                raise ValueError(f"Unsupported content block type: {block.type}")

        return LanguageModelResponse(message=response_text, usage=TokenUsage())

    def generate_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolCall]] = None,
        max_tokens: int = 256,
        temperature: float = 0.5,
        top_p: float = 1.0,
        **kwargs: Any,
    ) -> Iterator[LanguageModelResponse]:
        raise NotImplementedError(
            "AgentifyMe does not support Anthropic streaming yet."
        )

    def convert_messages_to_params(self, messages: List[Message]) -> List[MessageParam]:
        anthropic_messages: List[MessageParam] = []

        for message in messages:
            if message.content is None:
                continue

            # Prepare the content based on its type
            if isinstance(message.content, str):
                content = message.content
            elif isinstance(message.content, list):
                # Assuming content is a list of content blocks
                content = [
                    self.prepare_content_block(block) for block in message.content
                ]
            else:
                raise ValueError(f"Unsupported content type: {type(message.content)}")

            anthropic_message: MessageParam = {
                "role": "user" if message.role == Role.USER else "assistant",
                "content": content,
            }

            anthropic_messages.append(anthropic_message)

        return anthropic_messages

    def convert_content_block(self, block: dict) -> Union[str, dict]:
        if "type" not in block:
            raise ValueError("Content block is missing 'type' field")

        if block["type"] == "text":
            return block["text"]
        elif block["type"] == "image":
            return {
                "type": "image",
                "source": block.get("source"),
                "data": block.get("data"),
            }
        else:
            raise ValueError(f"Unsupported content block type: {block['type']}")

    def convert_params_to_messages(self, messages: List[MessageParam]) -> List[Message]:
        converted_messages: List[Message] = []

        for message in messages:
            role = Role.USER if message["role"] == "user" else Role.ASSISTANT

            # Handle content based on its type
            if isinstance(message["content"], str):
                content = message["content"]
            elif isinstance(message["content"], list):
                # Assuming content is a list of content blocks
                content = [
                    self.convert_content_block(block) for block in message["content"]
                ]
            else:
                raise ValueError(
                    f"Unsupported content type: {type(message['content'])}"
                )

            converted_message = Message(role=role, content=content)
            converted_messages.append(converted_message)

        return converted_messages

    def prepare_content_block(
        self, block: Union[str, dict]
    ) -> Union[
        TextBlockParam,
        ImageBlockParam,
        ToolUseBlockParam,
        ToolResultBlockParam,
        ContentBlock,
    ]:
        if isinstance(block, str):
            return {"type": "text", "text": block}
        elif isinstance(block, dict):
            block_type = block.get("type")
            if block_type == "text":
                return TextBlockParam(type="text", text=block["text"])
            elif block_type == "image":
                return ImageBlockParam(type="image", source=block["source"])
            # elif block_type == "tool_use":
            #     return ToolUseBlockParam(
            #         id=
            #         type="tool_use",
            #         tool_name=block["tool_name"],
            #         tool_input=block["tool_input"],
            #     )
            # elif block_type == "tool_result":
            #     return ToolResultBlockParam(
            #         type="tool_result",
            #         tool_name=block["tool_name"],
            #         tool_output=block["tool_output"],
            #     )
            else:
                # return block  # Assuming it's already a valid ContentBlock
                raise ValueError(f"Unsupported block type: {block_type}")
        else:
            raise ValueError(f"Unsupported block type: {type(block)}")
