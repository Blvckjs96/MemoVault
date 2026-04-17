"""Tests for STMStore."""

import json
from pathlib import Path

from memovault.core.stm_store import STMStore


class TestSTMStore:
    """Tests for session-scoped short-term memory store."""

    def _make_store(self, tmp_path: Path) -> STMStore:
        return STMStore(data_dir=tmp_path, session_id="test-session")

    def test_add_and_count(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("remember this", utility_score=2, decay_turns=5, category="constraint")
        assert store.count() == 1

    def test_get_active(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("low utility", utility_score=0, decay_turns=5)
        store.add("high utility", utility_score=3, decay_turns=5)
        active = store.get_active(min_utility=2)
        assert len(active) == 1
        assert active[0].content == "high utility"

    def test_get_context_items(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("low", utility_score=1, decay_turns=5)
        store.add("high", utility_score=2, decay_turns=5)
        store.add("higher", utility_score=3, decay_turns=5)
        context = store.get_context_items()
        assert len(context) == 2

    def test_eviction(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("ephemeral", utility_score=2, decay_turns=2)
        assert store.count() == 1
        store.increment_turn()  # turn 1
        store.increment_turn()  # turn 2
        assert store.count() == 1  # still within window (0+2=2 >= 2)
        store.increment_turn()  # turn 3 -> 3-0=3 > 2, evicted
        assert store.count() == 0

    def test_touch(self, tmp_path):
        store = self._make_store(tmp_path)
        item_id = store.add("test", utility_score=2, decay_turns=5)
        store.increment_turn()
        store.touch(item_id)
        item = store.get(item_id)
        assert item is not None
        assert item.last_accessed_turn == 1

    def test_clear(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("a", utility_score=1, decay_turns=5)
        store.add("b", utility_score=2, decay_turns=5)
        store.clear()
        assert store.count() == 0
        assert store.current_turn == 0

    def test_persistence(self, tmp_path):
        store1 = STMStore(data_dir=tmp_path, session_id="s1")
        store1.add("persisted", utility_score=3, decay_turns=10)
        store1.increment_turn()

        # Load from same dir
        store2 = STMStore(data_dir=tmp_path)
        assert store2.count() == 1
        assert store2.current_turn == 1
        items = store2.get_active()
        assert items[0].content == "persisted"

    def test_persistence_file_format(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("test", utility_score=2, decay_turns=5)
        path = tmp_path / "stm.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "session_id" in data
        assert "items" in data
        assert len(data["items"]) == 1

    def test_get_nonexistent(self, tmp_path):
        store = self._make_store(tmp_path)
        assert store.get("nonexistent") is None

    def test_to_dict(self, tmp_path):
        store = self._make_store(tmp_path)
        store.add("test", utility_score=1, decay_turns=3)
        d = store.to_dict()
        assert d["session_id"] == "test-session"
        assert d["total"] == 1
        assert len(d["items"]) == 1
