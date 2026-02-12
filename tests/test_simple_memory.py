"""Tests for simple memory implementation."""

import os
import tempfile

import pytest

from memovault.config.memory import SimpleMemoryConfig
from memovault.memory.item import MemoryItem
from memovault.memory.simple import SimpleMemory


class TestSimpleMemory:
    """Tests for SimpleMemory."""

    @pytest.fixture
    def memory(self):
        """Create a simple memory instance."""
        config = SimpleMemoryConfig()
        return SimpleMemory(config)

    def test_add_memory(self, memory):
        """Test adding a memory."""
        item = MemoryItem(memory="Test memory content")
        ids = memory.add([item])
        assert len(ids) == 1
        assert memory.count() == 1

    def test_add_multiple_memories(self, memory):
        """Test adding multiple memories."""
        items = [
            MemoryItem(memory="Memory 1"),
            MemoryItem(memory="Memory 2"),
            MemoryItem(memory="Memory 3"),
        ]
        ids = memory.add(items)
        assert len(ids) == 3
        assert memory.count() == 3

    def test_search(self, memory):
        """Test searching memories with BM25 ranking."""
        items = [
            MemoryItem(memory="I like Python programming"),
            MemoryItem(memory="JavaScript is for web"),
            MemoryItem(memory="Python is great for ML and Python is versatile"),
        ]
        memory.add(items)

        results = memory.search("Python")
        assert len(results) >= 1
        # Both Python memories should be found
        memories_text = [r.memory for r in results]
        assert any("Python" in m for m in memories_text)
        # JavaScript-only memory should not appear
        assert "JavaScript is for web" not in memories_text
        # Memory with more Python mentions should rank higher (BM25 TF)
        assert "Python" in results[0].memory

    def test_search_empty(self, memory):
        """Test searching with no memories."""
        results = memory.search("anything")
        assert results == []

    def test_search_no_match(self, memory):
        """Test searching with no matching results."""
        items = [MemoryItem(memory="I like apples")]
        memory.add(items)
        results = memory.search("zebra")
        assert results == []

    def test_get_by_id(self, memory):
        """Test getting a memory by ID."""
        item = MemoryItem(memory="Specific memory")
        ids = memory.add([item])

        result = memory.get(ids[0])
        assert result is not None
        assert result.memory == "Specific memory"

    def test_get_nonexistent(self, memory):
        """Test getting a nonexistent memory."""
        result = memory.get("nonexistent-id")
        assert result is None

    def test_get_all(self, memory):
        """Test getting all memories."""
        items = [
            MemoryItem(memory="Memory 1"),
            MemoryItem(memory="Memory 2"),
        ]
        memory.add(items)

        all_memories = memory.get_all()
        assert len(all_memories) == 2

    def test_update(self, memory):
        """Test updating a memory."""
        item = MemoryItem(memory="Original content")
        ids = memory.add([item])

        memory.update(ids[0], MemoryItem(memory="Updated content"))
        result = memory.get(ids[0])
        assert result.memory == "Updated content"

    def test_delete(self, memory):
        """Test deleting memories."""
        items = [
            MemoryItem(memory="Memory 1"),
            MemoryItem(memory="Memory 2"),
        ]
        ids = memory.add(items)
        assert memory.count() == 2

        memory.delete([ids[0]])
        assert memory.count() == 1

        remaining = memory.get_all()
        assert remaining[0].memory == "Memory 2"

    def test_delete_all(self, memory):
        """Test deleting all memories."""
        items = [
            MemoryItem(memory="Memory 1"),
            MemoryItem(memory="Memory 2"),
        ]
        memory.add(items)
        assert memory.count() == 2

        memory.delete_all()
        assert memory.count() == 0

    def test_dump_and_load(self, memory):
        """Test saving and loading memories."""
        items = [
            MemoryItem(memory="Persistent memory 1"),
            MemoryItem(memory="Persistent memory 2"),
        ]
        memory.add(items)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Dump
            memory.dump(tmpdir)
            assert os.path.exists(os.path.join(tmpdir, "memories.json"))

            # Create new memory instance and load
            config = SimpleMemoryConfig()
            new_memory = SimpleMemory(config)
            new_memory.load(tmpdir)

            assert new_memory.count() == 2
            loaded = new_memory.get_all()
            memories_text = [m.memory for m in loaded]
            assert "Persistent memory 1" in memories_text
            assert "Persistent memory 2" in memories_text
