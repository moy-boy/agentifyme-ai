from enum import Enum


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    COHERE = "cohere"
    VOYAGEAI = "voyageai"


class EmbeddingModelType(str, Enum):
    OPENAI_TEXT_EMBEDDING_3_SMALL = "openai/text-embedding-3-small"
    OPENAI_TEXT_EMBEDDING_3_LARGE = "openai/text-embedding-3-large"
    OPENAI_TEXT_EMBEDDING_ADA_002 = "openai/text-embedding-ada-002"
