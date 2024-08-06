from typing import Any, Dict, List
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class Document(BaseModel):
    """
    Class representing a document.
    """

    id: str = Field()
    content: str = Field(description="The content of the document.")
    metadata: Dict[str, Any] = Field(
        description="The metadata associated with the document."
    )


class VectorDocument(Document):
    """Represents a document with an embedding."""

    embedding: List[float] = SkipJsonSchema(Field())
