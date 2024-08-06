from typing import Optional
from agentifyme.document_stores.vector.base import VectorDocumentStore
from qdrant_client import QdrantClient


class QdrantVectorDocumentStore(VectorDocumentStore):

    def __init__(
        self,
        location: Optional[str] = None,
        url: Optional[str] = None,
        port: Optional[int] = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = False,
        api_key: Optional[str] = None,
        path: Optional[str] = None,
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
