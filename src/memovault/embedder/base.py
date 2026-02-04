"""Base embedder class for MemoVault."""

from abc import ABC, abstractmethod
from typing import Any


class BaseEmbedder(ABC):
    """Base class for all embedding models."""

    @abstractmethod
    def __init__(self, config: Any):
        """Initialize the embedding model with the given configuration."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for the given texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings, each represented as a list of floats.
        """

    def embed_one(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding as a list of floats.
        """
        return self.embed([text])[0]

    def _truncate_texts(self, texts: list[str], max_tokens: int | None = None) -> list[str]:
        """Truncate texts to fit within max_tokens limit.

        Args:
            texts: List of texts to truncate.
            max_tokens: Maximum number of tokens/characters.

        Returns:
            List of truncated texts.
        """
        if max_tokens is None:
            return texts

        # Simple character-based truncation (approximation)
        # Most models use ~4 chars per token on average
        max_chars = max_tokens * 4
        return [text[:max_chars] if len(text) > max_chars else text for text in texts]
