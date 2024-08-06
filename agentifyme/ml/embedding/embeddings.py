import os
from abc import ABC, abstractmethod
from typing import Any, Tuple, List, Dict, Optional, Union

import openai
from openai import NOT_GIVEN, OpenAI

from pydantic import BaseModel
from agentifyme.cache import cache, CacheType
from .providers import EmbeddingModelType


class Embedding(BaseModel):
    embedding: List[float]
    metadata: Dict[str, Any]


class EmbeddingModel(ABC):

    def __init__(
        self,
        embedding_model_type: EmbeddingModelType,
        dimensions: Optional[int] = None,
    ) -> None:
        self.embedding_model_type = embedding_model_type
        self.dimensions = dimensions

    @property
    def embedding_model_name(self) -> str:
        if "/" in self.embedding_model_type:
            return self.embedding_model_type.split("/")[-1]
        return self.embedding_model_type

    def __call__(
        self, text: Union[str, List[str]]
    ) -> Union[Embedding, List[Embedding]]:

        if isinstance(text, list):
            return self.run_batch(text)

        return self.run(text)

    def run(self, text: str) -> Embedding:
        embeddings = self.run_batch([text])
        return embeddings[0]

    @abstractmethod
    def run_batch(self, texts: List[str]) -> List[Embedding]:
        pass


class OpenAIEmbeddingModel(EmbeddingModel):

    def __init__(
        self,
        embedding_model_type: EmbeddingModelType,
        dimensions: Optional[int] = None,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 5,
        **kwargs
    ) -> None:
        super().__init__(
            embedding_model_type=embedding_model_type, dimensions=dimensions
        )

        _api_key = os.getenv("OPENAI_API_KEY") if api_key is None else api_key
        if not _api_key:
            raise ValueError("OpenAI API key is required")

        self.timeout = timeout
        if "OPENAI_MAX_RETRIES" in os.environ:
            self.timeout = float(os.environ.get("OPENAI_TIMEOUT", 30.0))

        self.max_retries = max_retries
        if "OPENAI_MAX_RETRIES" in os.environ:
            self.max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", 5))

        self.api_key = _api_key
        self.client = OpenAI(
            api_key=_api_key,
            base_url=api_base_url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
        )

    # @cache(CacheType.DISK)
    def run_batch(self, texts: List[str]) -> List[Embedding]:

        # Reference: https://platform.openai.com/docs/guides/embeddings/use-cases
        _texts = []
        for text in texts:
            text = text.replace("\n", " ")
            _texts.append(text)

        dimensions: int | openai.NOT_GIVEN = openai.NOT_GIVEN
        if self.dimensions is not None and self.dimensions > 0:
            dimensions = self.dimensions

        embedding_response = self.client.embeddings.create(
            input=_texts, model=self.embedding_model_name, dimensions=dimensions
        )

        embeddings = []
        for i, embedding in enumerate(embedding_response.data):
            embeddings.append(
                Embedding(
                    embedding=embedding.embedding,
                    metadata={"index": i, "object": "embedding"},
                )
            )

        return embeddings
