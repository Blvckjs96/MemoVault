"""Memory consolidation — find and merge near-duplicate memories."""

import json
from typing import Any

from memovault.llm.base import BaseLLM
from memovault.memory.item import MemoryItem
from memovault.utils.log import get_logger
from memovault.utils.prompts import CONSOLIDATION_PROMPT

logger = get_logger(__name__)


class MemoryConsolidator:
    """Finds near-duplicate memories and merges them using the LLM."""

    def __init__(self, llm: BaseLLM):
        self._llm = llm

    def consolidate(
        self,
        get_all_fn: Any,
        search_fn: Any,
        add_fn: Any,
        delete_fn: Any,
        similarity_threshold: float = 0.85,
    ) -> dict[str, Any]:
        """Find and merge near-duplicate memories.

        Args:
            get_all_fn: Callable returning all MemoryItems.
            search_fn: Callable for vector search (query, top_k, **kwargs).
            add_fn: Callable to add a MemoryItem (raw, bypasses scoring).
            delete_fn: Callable to delete memory IDs.
            similarity_threshold: Minimum similarity to consider duplicates.

        Returns:
            Stats dict with merged_groups and total_removed counts.
        """
        all_memories = get_all_fn()
        if len(all_memories) < 2:
            return {"merged_groups": 0, "total_removed": 0}

        seen_ids: set[str] = set()
        merged_groups = 0
        total_removed = 0

        for mem in all_memories:
            if mem.id in seen_ids:
                continue

            # Search for similar memories
            similar = search_fn(mem.memory, top_k=10)
            # Filter to those above threshold (and not self)
            group = [
                s for s in similar
                if s.id != mem.id and s.id not in seen_ids
                and getattr(s, "_score", 1.0) >= similarity_threshold
            ]

            if not group:
                continue

            # We have duplicates — merge them
            group_items = [mem] + group
            merged_text = self._merge(group_items)

            if not merged_text:
                continue

            # Delete all originals, add merged version
            ids_to_delete = [m.id for m in group_items]
            delete_fn(ids_to_delete)

            merged_item = MemoryItem(
                memory=merged_text,
                metadata=mem.metadata.model_copy(),
            )
            add_fn(merged_item)

            seen_ids.update(ids_to_delete)
            merged_groups += 1
            total_removed += len(ids_to_delete) - 1  # net reduction

        logger.info(
            f"Consolidation complete: {merged_groups} groups merged, "
            f"{total_removed} memories removed"
        )
        return {"merged_groups": merged_groups, "total_removed": total_removed}

    def _merge(self, items: list[MemoryItem]) -> str | None:
        """Use the LLM to merge a group of similar memories into one."""
        numbered = "\n".join(
            f"{i + 1}. {item.memory}" for i, item in enumerate(items)
        )
        messages = [
            {"role": "system", "content": CONSOLIDATION_PROMPT},
            {"role": "user", "content": numbered},
        ]
        try:
            result = self._llm.generate(messages)
            return result.strip()
        except Exception as e:
            logger.warning(f"LLM merge failed: {e}")
            return None

    def get_stats(
        self,
        get_all_fn: Any,
        search_fn: Any,
        similarity_threshold: float = 0.85,
    ) -> dict[str, Any]:
        """Return count of potential duplicate groups without modifying anything.

        Args:
            get_all_fn: Callable returning all MemoryItems.
            search_fn: Callable for vector search.
            similarity_threshold: Minimum similarity threshold.

        Returns:
            Dict with potential_groups and potential_duplicates counts.
        """
        all_memories = get_all_fn()
        if len(all_memories) < 2:
            return {"potential_groups": 0, "potential_duplicates": 0}

        seen_ids: set[str] = set()
        groups = 0
        duplicates = 0

        for mem in all_memories:
            if mem.id in seen_ids:
                continue

            similar = search_fn(mem.memory, top_k=10)
            group = [
                s for s in similar
                if s.id != mem.id and s.id not in seen_ids
            ]

            if group:
                groups += 1
                duplicates += len(group)
                seen_ids.add(mem.id)
                seen_ids.update(s.id for s in group)

        return {"potential_groups": groups, "potential_duplicates": duplicates}
