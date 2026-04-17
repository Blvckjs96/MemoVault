"""Tests for the SessionManager."""

from unittest.mock import MagicMock

from memovault.core.chat_history import ChatHistory
from memovault.core.session import SessionManager


class TestSessionManager:
    """Tests for session summarization and management."""

    def _make_manager(self, summary_response: str = "Session summary text") -> SessionManager:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = summary_response
        return SessionManager(llm=mock_llm)

    def test_summarize_session(self):
        mgr = self._make_manager("User discussed Python projects.")
        messages = [
            {"role": "user", "content": "I'm working on a Python project"},
            {"role": "assistant", "content": "Tell me more about it"},
        ]
        summary = mgr.summarize_session(messages)
        assert summary == "User discussed Python projects."

    def test_summarize_empty_messages(self):
        mgr = self._make_manager()
        assert mgr.summarize_session([]) == ""

    def test_end_session_with_history(self):
        mgr = self._make_manager("Summary of the session.")
        history = ChatHistory()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi there")

        added_items = []
        mock_add = lambda item: added_items.append(item)

        summary = mgr.end_session(chat_history=history, add_fn=mock_add)

        assert summary == "Summary of the session."
        assert len(added_items) == 1
        assert added_items[0].metadata.type == "session_summary"
        assert added_items[0].metadata.source == "system"
        assert history.total_messages == 0  # cleared

    def test_end_session_empty_history(self):
        mgr = self._make_manager()
        history = ChatHistory()
        mock_add = MagicMock()

        result = mgr.end_session(chat_history=history, add_fn=mock_add)
        assert result is None
        mock_add.assert_not_called()
