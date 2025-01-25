
from qdrant_client import QdrantClient

from agentifyme.document_stores.vector.base import VectorDocumentStore


class QdrantVectorDocumentStore(VectorDocumentStore):
    def __init__(
        self,
        location: str | None = None,
        url: str | None = None,
        port: int | None = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = False,
        api_key: str | None = None,
        path: str | None = None,
    ):
        self.client = QdrantClient(
            location=location,
            url=url,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            api_key=api_key,
            path=path,
        )
