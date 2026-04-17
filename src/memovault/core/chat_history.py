"""Chat history tracking for MemoVault with JSON persistence."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from memovault.utils.log import get_logger

logger = get_logger(__name__)

CHAT_HISTORY_FILENAME = "chat_history.json"


@dataclass
class ChatHistory:
    """Manages chat history for a session with optional disk persistence."""

    data_dir: str | Path | None = None
    session_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.data_dir is not None:
            self._path = Path(self.data_dir) / CHAT_HISTORY_FILENAME
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._load()
        else:
            self._path = None

    @property
    def total_messages(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    def _load(self) -> None:
        """Load chat history from disk."""
        if self._path and self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self.messages = data.get("messages", [])
                self.session_id = data.get("session_id")
                if data.get("created_at"):
                    self.created_at = datetime.fromisoformat(data["created_at"])
                logger.info(f"Chat history loaded: {len(self.messages)} messages")
            except Exception as e:
                logger.warning(f"Failed to load chat history: {e}")
                self.messages = []

    def _save(self) -> None:
        """Persist chat history to disk."""
        if self._path is None:
            return
        self._path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the history.

        Args:
            role: Message role (user, assistant, system).
            content: Message content.
        """
        self.messages.append({"role": role, "content": content})
        self._save()

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
        self._save()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "total_messages": self.total_messages,
            "messages": self.messages,
        }
