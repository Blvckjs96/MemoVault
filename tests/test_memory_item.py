"""Tests for memory item classes."""

import pytest

from memovault.memory.item import MemoryItem, MemoryMetadata


class TestMemoryMetadata:
    """Tests for MemoryMetadata."""

    def test_default_metadata(self):
        """Test default metadata creation."""
        meta = MemoryMetadata()
        assert meta.type is None
        assert meta.source == "conversation"
        assert meta.created_at is not None
        assert meta.updated_at is not None

    def test_metadata_with_values(self):
        """Test metadata with custom values."""
        meta = MemoryMetadata(type="fact", tags=["test", "example"])
        assert meta.type == "fact"
        assert meta.tags == ["test", "example"]

    def test_metadata_str(self):
        """Test metadata string representation."""
        meta = MemoryMetadata(type="preference")
        s = str(meta)
        assert "type=preference" in s


class TestMemoryItem:
    """Tests for MemoryItem."""

    def test_create_memory_item(self):
        """Test basic memory item creation."""
        item = MemoryItem(memory="Test memory")
        assert item.memory == "Test memory"
        assert item.id is not None
        assert isinstance(item.metadata, MemoryMetadata)

    def test_create_with_metadata(self):
        """Test memory item with custom metadata."""
        item = MemoryItem(
            memory="Test memory",
            metadata={"type": "fact", "source": "manual"},
        )
        assert item.memory == "Test memory"
        assert item.metadata.type == "fact"
        assert item.metadata.source == "manual"

    def test_from_dict(self):
        """Test creating memory from dict."""
        data = {
            "memory": "Test memory",
            "metadata": {"type": "event"},
        }
        item = MemoryItem.from_dict(data)
        assert item.memory == "Test memory"
        assert item.metadata.type == "event"

    def test_to_dict(self):
        """Test converting memory to dict."""
        item = MemoryItem(memory="Test memory")
        data = item.to_dict()
        assert data["memory"] == "Test memory"
        assert "id" in data
        assert "metadata" in data

    def test_str_representation(self):
        """Test string representation."""
        item = MemoryItem(memory="Short memory")
        s = str(item)
        assert "Short memory" in s
        assert item.id in s
