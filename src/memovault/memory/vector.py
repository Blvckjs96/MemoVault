"""Vector-based memory implementation for MemoVault."""

import json
import os
from typing import Any

from memovault.config.memory import VectorMemoryConfig
from memovault.embedder.factory import EmbedderFactory
from memovault.memory.base import BaseTextMemory
from memovault.memory.item import MemoryItem
from memovault.utils.log import get_logger
from memovault.vecdb.item import VecDBItem
from memovault.vecdb.qdrant import QdrantVecDB

logger = get_logger(__name__)


class VectorMemory(BaseTextMemory):
    """Vector-based memory implementation using embeddings and Qdrant.

    Uses semantic similarity for search via vector embeddings.
    Good for production use cases requiring accurate retrieval.
    """

    def __init__(self, config: VectorMemoryConfig):
        """Initialize vector memory.

        Args:
            config: Vector memory configuration.
        """
        self.config = config
        self.embedder = EmbedderFactory.from_config(config.embedder)
        self.vector_db = QdrantVecDB(config.vector_db)
        logger.info("VectorMemory initialized")

    def add(self, memories: list[MemoryItem | dict[str, Any]]) -> list[str]:
        """Add memories with embeddings.

        Args:
            memories: List of memories to add.

        Returns:
            List of memory IDs that were added.
        """
        if not memories:
            return []

        # Convert to MemoryItem if needed
        memory_items = [
            MemoryItem(**mem) if isinstance(mem, dict) else mem
            for mem in memories
        ]

        # Generate embeddings
        texts = [mem.memory for mem in memory_items]
        embeddings = self.embedder.embed(texts)

        # Create vector DB items
        vec_items = []
        for item, embedding in zip(memory_items, embeddings):
            vec_items.append(
                VecDBItem(
                    id=item.id,
                    vector=embedding,
                    payload=item.model_dump(),
                )
            )

        # Add to vector DB
        self.vector_db.add(vec_items)

        added_ids = [item.id for item in memory_items]
        logger.debug(f"Added {len(added_ids)} memories with embeddings")
        return added_ids

    def search(self, query: str, top_k: int = 5, **kwargs) -> list[MemoryItem]:
        """Search for memories using semantic similarity.

        Args:
            query: Search query.
            top_k: Number of results to return.
            **kwargs: Additional search parameters (e.g., filter).

        Returns:
            List of matching memories sorted by relevance.
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_one(query)

        # Search vector DB
        filter_dict = kwargs.get("filter")
        results = self.vector_db.search(query_embedding, top_k, filter=filter_dict)

        # Sort by score (higher is better)
        results = sorted(results, key=lambda x: x.score or 0, reverse=True)

        # Convert to MemoryItems
        memories = []
        for result in results:
            if result.payload:
                mem = MemoryItem(**result.payload)
                memories.append(mem)

        return memories

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            The memory item, or None if not found.
        """
        result = self.vector_db.get_by_id(memory_id)
        if result and result.payload:
            return MemoryItem(**result.payload)
        return None

    def get_all(self) -> list[MemoryItem]:
        """Get all memories.

        Returns:
            List of all memories.
        """
        results = self.vector_db.get_all()
        return [
            MemoryItem(**result.payload)
            for result in results
            if result.payload
        ]

    def update(self, memory_id: str, memory: MemoryItem | dict[str, Any]) -> None:
        """Update a memory.

        Args:
            memory_id: The memory ID to update.
            memory: The updated memory.
        """
        if isinstance(memory, dict):
            memory = MemoryItem(**memory)

        memory.id = memory_id

        # Generate new embedding
        embedding = self.embedder.embed_one(memory.memory)

        # Update in vector DB
        vec_item = VecDBItem(
            id=memory_id,
            vector=embedding,
            payload=memory.model_dump(),
        )
        self.vector_db.update(memory_id, vec_item)
        logger.debug(f"Updated memory: {memory_id}")

    def delete(self, memory_ids: list[str]) -> None:
        """Delete memories.

        Args:
            memory_ids: List of memory IDs to delete.
        """
        if memory_ids:
            self.vector_db.delete(memory_ids)
            logger.debug(f"Deleted {len(memory_ids)} memories")

    def delete_all(self) -> None:
        """Delete all memories."""
        self.vector_db.delete_all()
        logger.info("Deleted all memories")

    def count(self) -> int:
        """Count total memories.

        Returns:
            Number of memories.
        """
        return self.vector_db.count()

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
                raw_data = json.load(f)

            # Load VecDBItems
            vec_items = [VecDBItem.from_dict(item) for item in raw_data]
            self.vector_db.add(vec_items)

            logger.info(f"Loaded {len(vec_items)} memories from {memory_file}")

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

            # Get all items from vector DB
            all_items = self.vector_db.get_all()
            data = [item.to_dict() for item in all_items]

            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Dumped {len(data)} memories to {memory_file}")

        except Exception as e:
            logger.error(f"Error dumping memories: {e}")
            raise
