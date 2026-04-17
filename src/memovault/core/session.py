"""Session summarization and management for MemoVault."""

from typing import Any

from memovault.core.chat_history import ChatHistory
from memovault.llm.base import BaseLLM
from memovault.memory.item import MemoryItem, MemoryMetadata
from memovault.utils.log import get_logger
from memovault.utils.prompts import SESSION_SUMMARY_PROMPT

logger = get_logger(__name__)

SESSION_SUMMARY_TYPE = "session_summary"


class SessionManager:
    """Manages session lifecycle: summarization and storage."""

    def __init__(self, llm: BaseLLM):
        """Initialize the session manager.

        Args:
            llm: LLM instance for generating summaries.
        """
        self._llm = llm

    def summarize_session(self, messages: list[dict[str, str]]) -> str:
        """Summarize a list of chat messages into a concise session summary.

        Args:
            messages: Chat history messages (role/content dicts).

        Returns:
            A concise summary string.
        """
        if not messages:
            return ""

        conversation = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        )
        llm_messages = [
            {"role": "system", "content": SESSION_SUMMARY_PROMPT},
            {"role": "user", "content": conversation},
        ]

        try:
            summary = self._llm.generate(llm_messages)
            logger.debug("Session summary generated")
            return summary.strip()
        except Exception as e:
            logger.error(f"Session summarization failed: {e}")
            return ""

    def end_session(
        self,
        chat_history: ChatHistory,
        add_fn: Any,
    ) -> str | None:
        """Summarize the current session, store it as a memory, and clear history.

        Args:
            chat_history: The current chat history to summarize.
            add_fn: Callable that adds a MemoryItem to the vault (bypasses scoring).

        Returns:
            The summary string, or None if there was nothing to summarize.
        """
        messages = chat_history.get_messages()
        if not messages:
            return None

        summary = self.summarize_session(messages)
        if not summary:
            return None

        item = MemoryItem(
            memory=summary,
            metadata=MemoryMetadata(
                type=SESSION_SUMMARY_TYPE,
                source="system",
            ),
        )
        add_fn(item)
        chat_history.clear()
        logger.info("Session ended: summary stored and history cleared")
        return summary

    @staticmethod
    def get_recent_summaries(
        search_fn: Any,
        n: int = 3,
    ) -> list[MemoryItem]:
        """Retrieve recent session summaries from the vault.

        Args:
            search_fn: Callable that searches memories (query, top_k, **kwargs).
            n: Number of recent summaries to return.

        Returns:
            List of session summary MemoryItems.
        """
        results = search_fn(
            "session summary recap",
            top_k=n,
            filter={"metadata.type": SESSION_SUMMARY_TYPE},
        )
        return results
