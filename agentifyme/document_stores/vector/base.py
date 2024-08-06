from abc import ABC, abstractmethod
from typing import List

from agentifyme.document_stores.types import VectorDocument


class VectorDocumentStore(ABC):

    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collections in the document store.

        Returns:
            A list of collection names.
        """

    @abstractmethod
    def get_collection(self, collection_name: str) -> List[str]:
        """
        Get a collection from the document store.

        Args:
            collection_name: The name of the collection to retrieve.

        Returns:
            The collection.
        """

    @abstractmethod
    def get_document(self, collection_name: str, document_id: str) -> VectorDocument:
        """
        Get a document from the document store.

        Args:
            collection_name: The name of the collection to retrieve the document from.
            document_id: The ID of the document to retrieve.

        Returns:
            The document.
        """

    @abstractmethod
    def get_documents(self, collection_name: str) -> List[VectorDocument]:
        """
        Get all documents from a collection.

        Args:
            collection_name: The name of the collection to retrieve the documents from.

        Returns:
            A list of documents.
        """

    @abstractmethod
    def add_document(self, collection_name: str, document: VectorDocument):
        """
        Add a document to a collection.

        Args:
            collection_name: The name of the collection to add the document to.
            document: The document to add.

        Returns:
            None
        """

    @abstractmethod
    def delete_document(self, collection_name: str, document_id: str):
        """
        Delete a document from a collection.

        Args:
            collection_name: The name of the collection to delete the document from.
            document_id: The ID of the document to delete.

        Returns:
            None
        """

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """
        Delete a collection from the document store.

        Args:
            collection_name: The name of the collection to delete.

        Returns:
            None
        """
