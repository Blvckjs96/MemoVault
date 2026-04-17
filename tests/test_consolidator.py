"""Tests for the MemoryConsolidator."""

from unittest.mock import MagicMock

from memovault.core.consolidator import MemoryConsolidator
from memovault.memory.item import MemoryItem


class TestMemoryConsolidator:
    """Tests for memory deduplication/merging."""

    def _make_consolidator(self, merge_response: str = "Merged memory") -> MemoryConsolidator:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = merge_response
        return MemoryConsolidator(llm=mock_llm)

    def test_consolidate_no_memories(self):
        cons = self._make_consolidator()
        result = cons.consolidate(
            get_all_fn=lambda: [],
            search_fn=MagicMock(),
            add_fn=MagicMock(),
            delete_fn=MagicMock(),
        )
        assert result["merged_groups"] == 0
        assert result["total_removed"] == 0

    def test_consolidate_single_memory(self):
        cons = self._make_consolidator()
        mem = MemoryItem(memory="Only one memory")
        result = cons.consolidate(
            get_all_fn=lambda: [mem],
            search_fn=MagicMock(),
            add_fn=MagicMock(),
            delete_fn=MagicMock(),
        )
        assert result["merged_groups"] == 0

    def test_get_stats_empty(self):
        cons = self._make_consolidator()
        stats = cons.get_stats(
            get_all_fn=lambda: [],
            search_fn=MagicMock(),
        )
        assert stats["potential_groups"] == 0
        assert stats["potential_duplicates"] == 0

    def test_merge_uses_llm(self):
        cons = self._make_consolidator("Combined fact about Python and coding")
        items = [
            MemoryItem(memory="User likes Python"),
            MemoryItem(memory="User prefers Python for coding"),
        ]
        result = cons._merge(items)
        assert result == "Combined fact about Python and coding"
