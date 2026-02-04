"""Main MemoVault class - the primary interface for the memory system."""

from typing import Any

from memovault.config.llm import LLMConfig
from memovault.config.memory import MemoryConfig
from memovault.config.settings import Settings, get_settings
from memovault.core.chat_history import ChatHistory
from memovault.core.mem_cube import MemCube
from memovault.llm.factory import LLMFactory
from memovault.memory.item import MemoryItem
from memovault.utils.log import get_logger
from memovault.utils.prompts import CHAT_SYSTEM_PROMPT

logger = get_logger(__name__)


class MemoVault:
    """MemoVault - A simplified personal memory system.

    This is the main interface for interacting with the memory system.
    It provides methods for adding, searching, and chatting with memories.

    Example:
        >>> from memovault import MemoVault
        >>> mem = MemoVault()
        >>> mem.add("I prefer Python for backend development")
        >>> results = mem.search("programming preferences")
        >>> response = mem.chat("What language should I use?")
    """

    def __init__(
        self,
        settings: Settings | None = None,
        memory_config: MemoryConfig | None = None,
        llm_config: LLMConfig | None = None,
    ):
        """Initialize MemoVault.

        Args:
            settings: Optional settings (defaults to environment-based settings).
            memory_config: Optional memory configuration (overrides settings).
            llm_config: Optional LLM configuration (overrides settings).
        """
        self.settings = settings or get_settings()

        # Initialize memory
        if memory_config:
            self._memory_config = memory_config
        else:
            self._memory_config = MemoryConfig.from_settings(self.settings)

        self._cube = MemCube(self._memory_config)

        # Initialize LLM
        if llm_config:
            self._llm_config = llm_config
        else:
            self._llm_config = LLMConfig.from_settings(self.settings)

        self._llm = LLMFactory.from_config(self._llm_config)

        # Chat history
        self._chat_history = ChatHistory()

        logger.info("MemoVault initialized")

    # =========================================================================
    # Memory Operations
    # =========================================================================

    def add(
        self,
        content: str | list[str] | MemoryItem | list[MemoryItem],
        **metadata: Any,
    ) -> list[str]:
        """Add memories.

        Args:
            content: Memory content (string, list of strings, or MemoryItem).
            **metadata: Additional metadata to attach to memories.

        Returns:
            List of memory IDs that were added.

        Example:
            >>> mem.add("I prefer dark mode")
            >>> mem.add(["Fact 1", "Fact 2"], type="fact")
        """
        # Normalize input to list
        if isinstance(content, str):
            items = [MemoryItem(memory=content, metadata=metadata)]
        elif isinstance(content, MemoryItem):
            items = [content]
        elif isinstance(content, list):
            items = []
            for item in content:
                if isinstance(item, str):
                    items.append(MemoryItem(memory=item, metadata=metadata))
                elif isinstance(item, MemoryItem):
                    items.append(item)
                else:
                    items.append(MemoryItem(**item))
        else:
            items = [MemoryItem(**content)]

        return self._cube.add(items)

    def search(self, query: str, top_k: int = 5, **kwargs) -> list[MemoryItem]:
        """Search for relevant memories.

        Args:
            query: Search query.
            top_k: Number of results to return.
            **kwargs: Additional search parameters.

        Returns:
            List of matching memories sorted by relevance.

        Example:
            >>> results = mem.search("programming preferences")
            >>> for r in results:
            ...     print(r.memory)
        """
        return self._cube.search(query, top_k, **kwargs)

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a specific memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            The memory item, or None if not found.
        """
        return self._cube.get(memory_id)

    def get_all(self) -> list[MemoryItem]:
        """Get all memories.

        Returns:
            List of all memories.
        """
        return self._cube.get_all()

    def update(self, memory_id: str, content: str | MemoryItem, **metadata: Any) -> None:
        """Update a memory.

        Args:
            memory_id: The memory ID to update.
            content: New content (string or MemoryItem).
            **metadata: Additional metadata.
        """
        if isinstance(content, str):
            content = MemoryItem(memory=content, metadata=metadata)
        self._cube.update(memory_id, content)

    def delete(self, memory_id: str | list[str]) -> None:
        """Delete memories.

        Args:
            memory_id: Single ID or list of IDs to delete.
        """
        self._cube.delete(memory_id)

    def delete_all(self) -> None:
        """Delete all memories."""
        self._cube.delete_all()

    def count(self) -> int:
        """Count total memories.

        Returns:
            Number of memories.
        """
        return self._cube.count()

    # =========================================================================
    # Chat Operations
    # =========================================================================

    def chat(
        self,
        query: str,
        top_k: int = 5,
        system_prompt: str | None = None,
        include_history: bool = True,
    ) -> str:
        """Chat with memory-enhanced responses.

        Searches for relevant memories and uses them as context for the LLM.

        Args:
            query: User's query.
            top_k: Number of memories to include as context.
            system_prompt: Optional custom system prompt (can include {memories_section}).
            include_history: Whether to include chat history.

        Returns:
            Assistant's response.

        Example:
            >>> response = mem.chat("What language should I use for my backend?")
            >>> print(response)
        """
        # Search for relevant memories
        memories = self._cube.search(query, top_k)

        # Build memories section
        if memories:
            memory_lines = [f"- {mem.memory}" for mem in memories]
            memories_section = "## Relevant Memories:\n" + "\n".join(memory_lines)
        else:
            memories_section = ""

        # Build system prompt
        if system_prompt:
            system_content = system_prompt.format(memories_section=memories_section)
        else:
            system_content = CHAT_SYSTEM_PROMPT.format(memories_section=memories_section)

        # Build messages
        messages = [{"role": "system", "content": system_content}]

        if include_history:
            messages.extend(self._chat_history.get_messages())

        messages.append({"role": "user", "content": query})

        # Generate response
        response = self._llm.generate(messages)

        # Update chat history
        self._chat_history.add_user_message(query)
        self._chat_history.add_assistant_message(response)

        logger.debug(f"Chat response generated with {len(memories)} memories as context")
        return response

    def clear_chat_history(self) -> None:
        """Clear the chat history."""
        self._chat_history.clear()
        logger.debug("Chat history cleared")

    def get_chat_history(self) -> list[dict[str, str]]:
        """Get the chat history.

        Returns:
            List of chat messages.
        """
        return self._chat_history.get_messages()

    # =========================================================================
    # Persistence
    # =========================================================================

    def dump(self, path: str) -> None:
        """Save memories to disk.

        Args:
            path: Directory path to save to.
        """
        self._cube.dump(path)
        logger.info(f"MemoVault saved to {path}")

    def load(self, path: str) -> None:
        """Load memories from disk.

        Args:
            path: Directory path to load from.
        """
        self._cube.load(path)
        logger.info(f"MemoVault loaded from {path}")

    @classmethod
    def from_path(cls, path: str, settings: Settings | None = None) -> "MemoVault":
        """Load MemoVault from a saved directory.

        Args:
            path: Directory path containing saved MemoVault.
            settings: Optional settings for LLM configuration.

        Returns:
            Loaded MemoVault instance.
        """
        cube = MemCube.load_from_path(path)

        instance = cls.__new__(cls)
        instance.settings = settings or get_settings()
        instance._memory_config = cube.config
        instance._cube = cube
        instance._llm_config = LLMConfig.from_settings(instance.settings)
        instance._llm = LLMFactory.from_config(instance._llm_config)
        instance._chat_history = ChatHistory()

        logger.info(f"MemoVault loaded from {path}")
        return instance

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def cube(self) -> MemCube:
        """Get the underlying MemCube."""
        return self._cube
