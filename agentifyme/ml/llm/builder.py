import importlib.util
from typing import Optional

from pydantic import BaseModel, field_validator

from agentifyme.cache import Cache, CacheType, DiskCache, MemoryCache
from agentifyme.utilities.env import load_env_file

from .anthropic import AnthropicLanguageModel
from .base import LanguageModel, LanguageModelProvider, LanguageModelType
from .groq import GroqLanguageModel
from .openai import OpenAILanguageModel


class LanguageModelConfig(BaseModel):
    model: LanguageModelType
    cache_type: CacheType = CacheType.NONE
    max_retries: int = 3
    prompt_template: str = ""
    verbose: int = 0
    system_prompt: Optional[str] = ""
    api_key: Optional[str] = None
    temparature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 1024
    json_mode: bool = False

    organization: Optional[str] = None
    project: Optional[str] = None

    env_file: Optional[str] = None

    @property
    def provider(self) -> Optional[LanguageModelProvider]:
        model_prefix = self.model.value.split("/")[0]
        try:
            return LanguageModelProvider(model_prefix)
        except ValueError:
            return None

    @field_validator("env_file")
    def load_env_vars(cls, v):
        if v is not None:
            # Load environment variables from the specified file
            load_env_file(v)


class LanguageModelBuilder:
    def __init__(self, config: LanguageModelConfig) -> None:
        self.config = config

    def create_cache(self) -> Cache:
        if self.config.cache_type == CacheType.MEMORY:
            return MemoryCache()
        elif self.config.cache_type == CacheType.DISK:
            return DiskCache()
        else:
            return MemoryCache()  # Default to memory cache

    def create_llm(self) -> LanguageModel:
        cache_strategy = self.create_cache()
        if self.config.provider == LanguageModelProvider.OPENAI:
            if importlib.util.find_spec("openai") is not None:
                return OpenAILanguageModel(
                    llm_model=self.config.model,
                    api_key=self.config.api_key,
                    system_prompt=self.config.system_prompt,
                    llm_cache_type=self.config.cache_type,
                    cache_strategy=cache_strategy,
                    verbose=self.config.verbose,
                    json_mode=self.config.json_mode,
                    organization=self.config.organization,
                    project=self.config.project,
                )
            else:
                raise ImportError(
                    "The 'openai' package is not installed. Please install it to use OpenAI models."
                )

        elif self.config.provider == LanguageModelProvider.GROQ:
            if importlib.util.find_spec("groq") is not None:
                return GroqLanguageModel(
                    llm_model=self.config.model,
                    api_key=self.config.api_key,
                    system_prompt=self.config.system_prompt,
                    llm_cache_type=self.config.cache_type,
                    verbose=self.config.verbose,
                )
            else:
                raise ImportError(
                    "The 'groq' package is not installed. Please install it to use Groq models."
                )

        elif self.config.provider == LanguageModelProvider.ANTHROPIC:
            if importlib.util.find_spec("anthropic") is not None:
                return AnthropicLanguageModel(
                    llm_model=self.config.model,
                    api_key=self.config.api_key,
                    system_prompt=self.config.system_prompt,
                    llm_cache_type=self.config.cache_type,
                    verbose=self.config.verbose,
                )
            else:
                raise ImportError(
                    "The 'anthropic' package is not installed. Please install it to use Anthropic models."
                )
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")


def get_language_model(config: LanguageModelConfig) -> LanguageModel:
    builder = LanguageModelBuilder(config)
    return builder.create_llm()
