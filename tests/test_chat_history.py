"""Tests for chat history."""

import pytest

from memovault.core.chat_history import ChatHistory


class TestChatHistory:
    """Tests for ChatHistory."""

    def test_create_history(self):
        """Test creating chat history."""
        history = ChatHistory(session_id="test-session")
        assert history.session_id == "test-session"
        assert history.total_messages == 0

    def test_add_messages(self):
        """Test adding messages."""
        history = ChatHistory()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi there!")

        assert history.total_messages == 2
        messages = history.get_messages()
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"

    def test_get_limited_messages(self):
        """Test getting limited messages."""
        history = ChatHistory()
        history.add_user_message("Message 1")
        history.add_assistant_message("Response 1")
        history.add_user_message("Message 2")
        history.add_assistant_message("Response 2")

        # Get last 2 messages
        messages = history.get_messages(limit=2)
        assert len(messages) == 2
        assert messages[0]["content"] == "Message 2"

    def test_clear_history(self):
        """Test clearing history."""
        history = ChatHistory()
        history.add_user_message("Test message")
        assert history.total_messages == 1

        history.clear()
        assert history.total_messages == 0

    def test_to_dict(self):
        """Test converting to dictionary."""
        history = ChatHistory(session_id="test")
        history.add_user_message("Hello")

        data = history.to_dict()
        assert data["session_id"] == "test"
        assert data["total_messages"] == 1
        assert len(data["messages"]) == 1
