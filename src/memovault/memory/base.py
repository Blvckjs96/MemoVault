"""Base memory class for MemoVault."""

from abc import ABC, abstractmethod
from typing import Any

from memovault.memory.item import MemoryItem


class BaseTextMemory(ABC):
    """Base class for all textual memory implementations."""

    @abstractmethod
    def __init__(self, config: Any):
        """Initialize memory with the given configuration."""

    @abstractmethod
    def add(self, memories: list[MemoryItem | dict[str, Any]]) -> list[str]:
        """Add memories.

        Args:
            memories: List of MemoryItem objects or dictionaries.

        Returns:
            List of memory IDs that were added.
        """

    @abstractmethod
    def search(self, query: str, top_k: int = 5, **kwargs) -> list[MemoryItem]:
        """Search for memories based on a query.

        Args:
            query: Search query.
            top_k: Number of results to return.
            **kwargs: Additional search parameters.

        Returns:
            List of matching memories.
        """

    @abstractmethod
    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            The memory item, or None if not found.
        """

    @abstractmethod
    def get_all(self) -> list[MemoryItem]:
        """Get all memories.

        Returns:
            List of all memories.
        """

    @abstractmethod
    def update(self, memory_id: str, memory: MemoryItem | dict[str, Any]) -> None:
        """Update a memory.

        Args:
            memory_id: The memory ID to update.
            memory: The updated memory.
        """

    @abstractmethod
    def delete(self, memory_ids: list[str]) -> None:
        """Delete memories.

        Args:
            memory_ids: List of memory IDs to delete.
        """

    @abstractmethod
    def delete_all(self) -> None:
        """Delete all memories."""

    @abstractmethod
    def count(self) -> int:
        """Count total memories.

        Returns:
            Number of memories.
        """

    @abstractmethod
    def load(self, path: str) -> None:
        """Load memories from disk.

        Args:
            path: Directory path to load from.
        """

    @abstractmethod
    def dump(self, path: str) -> None:
        """Dump memories to disk.

        Args:
            path: Directory path to dump to.
        """
