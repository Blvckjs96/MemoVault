"""Simple JSON-based memory implementation for MemoVault."""

import json
import os
from typing import Any

from rank_bm25 import BM25Okapi

from memovault.config.memory import SimpleMemoryConfig
from memovault.memory.base import BaseTextMemory
from memovault.memory.item import MemoryItem
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class SimpleMemory(BaseTextMemory):
    """Simple JSON-based memory implementation.

    Uses BM25 ranking for search (no vector embeddings).
    Good for lightweight use cases or when embeddings aren't available.
    """

    def __init__(self, config: SimpleMemoryConfig):
        """Initialize simple memory.

        Args:
            config: Simple memory configuration.
        """
        self.config = config
        self.memories: list[dict[str, Any]] = []
        logger.info("SimpleMemory initialized")

    def add(self, memories: list[MemoryItem | dict[str, Any]]) -> list[str]:
        """Add memories.

        Args:
            memories: List of memories to add.

        Returns:
            List of memory IDs that were added.
        """
        added_ids = []
        for mem in memories:
            if isinstance(mem, dict):
                mem = MemoryItem(**mem)

            memory_dict = mem.model_dump()

            # Check for duplicates
            if memory_dict["id"] not in [m["id"] for m in self.memories]:
                self.memories.append(memory_dict)
                added_ids.append(memory_dict["id"])
                logger.debug(f"Added memory: {memory_dict['id']}")

        return added_ids

    def search(self, query: str, top_k: int = 5, **kwargs) -> list[MemoryItem]:
        """Search for memories using BM25 ranking.

        Args:
            query: Search query.
            top_k: Number of results to return.

        Returns:
            List of matching memories ranked by BM25 relevance.
        """
        if not self.memories:
            return []

        # Tokenize all memories for BM25
        corpus = [mem["memory"].lower().split() for mem in self.memories]
        bm25 = BM25Okapi(corpus)

        # Score query against corpus
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Pair memories with scores, filter out zero-score results
        scored = [
            (mem, score)
            for mem, score in zip(self.memories, scores)
            if score > 0
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [MemoryItem(**mem) for mem, _ in scored[:top_k]]

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            The memory item, or None if not found.
        """
        for memory in self.memories:
            if memory["id"] == memory_id:
                return MemoryItem(**memory)
        return None

    def get_all(self) -> list[MemoryItem]:
        """Get all memories.

        Returns:
            List of all memories.
        """
        return [MemoryItem(**mem) for mem in self.memories]

    def update(self, memory_id: str, memory: MemoryItem | dict[str, Any]) -> None:
        """Update a memory.

        Args:
            memory_id: The memory ID to update.
            memory: The updated memory.
        """
        if isinstance(memory, dict):
            memory = MemoryItem(**memory)

        memory.id = memory_id
        memory_dict = memory.model_dump()

        for i, mem in enumerate(self.memories):
            if mem["id"] == memory_id:
                self.memories[i] = memory_dict
                logger.debug(f"Updated memory: {memory_id}")
                return

        logger.warning(f"Memory not found for update: {memory_id}")

    def delete(self, memory_ids: list[str]) -> None:
        """Delete memories.

        Args:
            memory_ids: List of memory IDs to delete.
        """
        self.memories = [m for m in self.memories if m["id"] not in memory_ids]
        logger.debug(f"Deleted {len(memory_ids)} memories")

    def delete_all(self) -> None:
        """Delete all memories."""
        count = len(self.memories)
        self.memories = []
        logger.info(f"Deleted all {count} memories")

    def count(self) -> int:
        """Count total memories.

        Returns:
            Number of memories.
        """
        return len(self.memories)

    def load(self, path: str) -> None:
        """Load memories from disk.

        Args:
            path: Directory path to load from.
        """
        try:
            memory_file = os.path.join(path, self.config.memory_filename)
            if not os.path.exists(memory_file):
                logger.warning(f"Memory file not found: {memory_file}")
                return

            with open(memory_file, encoding="utf-8") as f:
                raw_memories = json.load(f)

            # Add loaded memories
            for mem in raw_memories:
                if mem["id"] not in [m["id"] for m in self.memories]:
                    self.memories.append(mem)

            logger.info(f"Loaded {len(raw_memories)} memories from {memory_file}")

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logger.error(f"Error loading memories: {e}")

    def dump(self, path: str) -> None:
        """Dump memories to disk.

        Args:
            path: Directory path to dump to.
        """
        try:
            os.makedirs(path, exist_ok=True)
            memory_file = os.path.join(path, self.config.memory_filename)

            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)

            logger.info(f"Dumped {len(self.memories)} memories to {memory_file}")

        except Exception as e:
            logger.error(f"Error dumping memories: {e}")
            raise
