"""Session-scoped short-term memory store with JSON persistence."""

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from memovault.utils.log import get_logger

logger = get_logger(__name__)

STM_FILENAME = "stm.json"


@dataclass
class STMItem:
    """A single short-term memory item."""

    id: str
    session_id: str
    content: str
    utility_score: int  # 0-3
    decay_turns: int
    category: str  # constraint, definition, goal, assumption, environment
    created_turn: int
    last_accessed_turn: int
    created_at: str


@dataclass
class STMStore:
    """Session-scoped short-term memory with JSON persistence.

    STM items auto-evict when current_turn - created_turn > decay_turns.
    No embeddings needed — session-local, small set.
    """

    data_dir: str | Path
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _items: list[STMItem] = field(default_factory=list, repr=False)
    _current_turn: int = field(default=0, repr=False)
    _recent_hashes: dict = field(default_factory=dict, repr=False)  # hash -> epoch_ts

    _DEDUP_WINDOW_SECONDS: float = field(default=30.0, repr=False)

    def __post_init__(self) -> None:
        self._data_dir = Path(self.data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._data_dir / STM_FILENAME
        self._load()

    @property
    def current_turn(self) -> int:
        return self._current_turn

    def increment_turn(self) -> None:
        """Advance the turn counter and evict expired items."""
        self._current_turn += 1
        self._evict_expired()
        self._save()

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(f"{self.session_id}:{content}".encode()).hexdigest()

    def _is_duplicate(self, content: str) -> bool:
        """Return True if identical content was written within the dedup window."""
        now = time.monotonic()
        h = self._content_hash(content)
        # Prune stale entries
        self._recent_hashes = {k: v for k, v in self._recent_hashes.items() if now - v < self._DEDUP_WINDOW_SECONDS}
        return h in self._recent_hashes

    def _register_hash(self, content: str) -> None:
        self._recent_hashes[self._content_hash(content)] = time.monotonic()

    def add(
        self,
        content: str,
        utility_score: int,
        decay_turns: int,
        category: str = "constraint",
    ) -> str:
        """Add a new STM item, skipping duplicates within the dedup window.

        Returns:
            The new item's ID (or existing duplicate's virtual ID if skipped).
        """
        if self._is_duplicate(content):
            logger.debug("STM dedup: skipping duplicate content within 30s window")
            return ""

        item_id = str(uuid.uuid4())
        item = STMItem(
            id=item_id,
            session_id=self.session_id,
            content=content,
            utility_score=utility_score,
            decay_turns=decay_turns,
            category=category,
            created_turn=self._current_turn,
            last_accessed_turn=self._current_turn,
            created_at=datetime.now().isoformat(),
        )
        self._items.append(item)
        self._register_hash(content)
        self._save()
        logger.debug(f"STM added: utility={utility_score}, decay={decay_turns}, cat={category}")
        return item_id

    def get_active(self, min_utility: int = 0) -> list[STMItem]:
        """Get all non-expired items with utility >= min_utility."""
        self._evict_expired()
        return [i for i in self._items if i.utility_score >= min_utility]

    def get_context_items(self) -> list[STMItem]:
        """Get items suitable for chat context (utility >= 2)."""
        return self.get_active(min_utility=2)

    def touch(self, item_id: str) -> None:
        """Mark an item as accessed this turn."""
        for item in self._items:
            if item.id == item_id:
                item.last_accessed_turn = self._current_turn
                break
        self._save()

    def get(self, item_id: str) -> STMItem | None:
        """Get a single item by ID."""
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def get_all(self) -> list[STMItem]:
        """Get all items (including expired, before eviction)."""
        return list(self._items)

    def count(self) -> int:
        """Count active items."""
        return len(self._items)

    def clear(self) -> None:
        """Clear all STM items and reset turn counter."""
        self._items = []
        self._current_turn = 0
        self._save()
        logger.debug("STM cleared")

    def _evict_expired(self) -> None:
        """Remove items past their decay window."""
        before = len(self._items)
        self._items = [
            i for i in self._items
            if (self._current_turn - i.created_turn) <= i.decay_turns
        ]
        evicted = before - len(self._items)
        if evicted > 0:
            logger.debug(f"STM evicted {evicted} expired items")

    def _load(self) -> None:
        """Load STM state from disk."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._current_turn = data.get("current_turn", 0)
                self.session_id = data.get("session_id", self.session_id)
                self._items = [STMItem(**item) for item in data.get("items", [])]
                logger.info(f"STM loaded: {len(self._items)} items, turn {self._current_turn}")
            except Exception as e:
                logger.warning(f"Failed to load STM: {e}")
                self._items = []

    def _save(self) -> None:
        """Persist STM state to disk."""
        data = {
            "session_id": self.session_id,
            "current_turn": self._current_turn,
            "items": [asdict(item) for item in self._items],
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "current_turn": self._current_turn,
            "total": len(self._items),
            "items": [asdict(item) for item in self._items],
        }
