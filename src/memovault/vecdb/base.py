"""Base vector database class for MemoVault."""

from abc import ABC, abstractmethod
from typing import Any

from memovault.vecdb.item import VecDBItem


class BaseVecDB(ABC):
    """Base class for all vector databases."""

    @abstractmethod
    def __init__(self, config: Any):
        """Initialize the vector database with the given configuration."""

    # Collection management

    @abstractmethod
    def create_collection(self) -> None:
        """Create a new collection/index."""

    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all collections."""

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        """Delete a collection."""

    @abstractmethod
    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""

    # Vector operations

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filter: dict[str, Any] | None = None,
    ) -> list[VecDBItem]:
        """Search for similar items.

        Args:
            query_vector: Vector to search for.
            top_k: Number of results to return.
            filter: Optional payload filters.

        Returns:
            List of search results with similarity scores.
        """

    @abstractmethod
    def get_by_id(self, id: str) -> VecDBItem | None:
        """Get an item by ID."""

    @abstractmethod
    def get_by_ids(self, ids: list[str]) -> list[VecDBItem]:
        """Get multiple items by their IDs."""

    @abstractmethod
    def get_all(self) -> list[VecDBItem]:
        """Get all items in the collection."""

    @abstractmethod
    def count(self) -> int:
        """Count items in the collection."""

    @abstractmethod
    def add(self, data: list[VecDBItem]) -> None:
        """Add items to the collection."""

    @abstractmethod
    def update(self, id: str, data: VecDBItem) -> None:
        """Update an item in the collection."""

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """Delete items from the collection."""

    @abstractmethod
    def delete_all(self) -> None:
        """Delete all items from the collection."""
