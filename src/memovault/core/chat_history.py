"""Chat history tracking for MemoVault."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatHistory:
    """Manages chat history for a session."""

    session_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    messages: list[dict[str, str]] = field(default_factory=list)

    @property
    def total_messages(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the history.

        Args:
            role: Message role (user, assistant, system).
            content: Message content.
        """
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message("assistant", content)

    def get_messages(self, limit: int | None = None) -> list[dict[str, str]]:
        """Get messages from history.

        Args:
            limit: Maximum number of recent messages to return.

        Returns:
            List of messages.
        """
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:]

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "total_messages": self.total_messages,
            "messages": self.messages,
        }
