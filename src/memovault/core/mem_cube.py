"""Memory container (MemCube) for MemoVault."""

import json
import os
from typing import Any

from memovault.config.memory import MemoryConfig
from memovault.memory.base import BaseTextMemory
from memovault.memory.factory import MemoryFactory
from memovault.memory.item import MemoryItem
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class MemCube:
    """Memory container that wraps a text memory implementation.

    Provides a simple interface for memory operations with optional
    persistence support.
    """

    def __init__(self, config: MemoryConfig):
        """Initialize MemCube.

        Args:
            config: Memory configuration.
        """
        self.config = config
        self._memory: BaseTextMemory = MemoryFactory.from_config(config)
        logger.info(f"MemCube initialized with {config.backend} backend")

    @property
    def memory(self) -> BaseTextMemory:
        """Get the underlying memory implementation."""
        return self._memory

    def add(self, memories: list[MemoryItem | dict[str, Any] | str]) -> list[str]:
        """Add memories to the cube.

        Args:
            memories: List of memories (MemoryItem, dict, or string).

        Returns:
            List of memory IDs that were added.
        """
        # Convert strings to MemoryItem
        items = []
        for mem in memories:
            if isinstance(mem, str):
                items.append(MemoryItem(memory=mem))
            elif isinstance(mem, dict):
                items.append(MemoryItem(**mem))
            else:
                items.append(mem)

        return self._memory.add(items)

    def search(self, query: str, top_k: int = 5, **kwargs) -> list[MemoryItem]:
        """Search for relevant memories.

        Args:
            query: Search query.
            top_k: Number of results to return.
            **kwargs: Additional search parameters.

        Returns:
            List of matching memories.
        """
        return self._memory.search(query, top_k, **kwargs)

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            The memory item, or None if not found.
        """
        return self._memory.get(memory_id)

    def get_all(self) -> list[MemoryItem]:
        """Get all memories.

        Returns:
            List of all memories.
        """
        return self._memory.get_all()

    def update(self, memory_id: str, memory: MemoryItem | dict[str, Any] | str) -> None:
        """Update a memory.

        Args:
            memory_id: The memory ID to update.
            memory: The updated memory.
        """
        if isinstance(memory, str):
            memory = MemoryItem(memory=memory)
        self._memory.update(memory_id, memory)

    def delete(self, memory_id: str | list[str]) -> None:
        """Delete memories.

        Args:
            memory_id: Single ID or list of IDs to delete.
        """
        if isinstance(memory_id, str):
            memory_id = [memory_id]
        self._memory.delete(memory_id)

    def delete_all(self) -> None:
        """Delete all memories."""
        self._memory.delete_all()

    def count(self) -> int:
        """Count total memories.

        Returns:
            Number of memories.
        """
        return self._memory.count()

    def load(self, path: str) -> None:
        """Load memories from disk.

        Args:
            path: Directory path to load from.
        """
        self._memory.load(path)

    def dump(self, path: str) -> None:
        """Dump memories to disk.

        Args:
            path: Directory path to dump to.
        """
        os.makedirs(path, exist_ok=True)

        # Save config
        config_path = os.path.join(path, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config.model_dump(), f, indent=2)

        # Save memories
        self._memory.dump(path)
        logger.info(f"MemCube dumped to {path}")

    @classmethod
    def load_from_path(cls, path: str) -> "MemCube":
        """Load a MemCube from a directory.

        Args:
            path: Directory path containing the saved MemCube.

        Returns:
            Loaded MemCube instance.
        """
        config_path = os.path.join(path, "config.json")

        with open(config_path, encoding="utf-8") as f:
            config_data = json.load(f)

        config = MemoryConfig.model_validate(config_data)
        cube = cls(config)
        cube.load(path)

        logger.info(f"MemCube loaded from {path}")
        return cube
