"""OpenAI embedder implementation for MemoVault."""

import openai

from memovault.config.embedder import OpenAIEmbedderConfig
from memovault.embedder.base import BaseEmbedder
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedder implementation."""

    def __init__(self, config: OpenAIEmbedderConfig):
        """Initialize the OpenAI embedder.

        Args:
            config: OpenAI embedder configuration.
        """
        self.config = config
        self.client = openai.Client(
            api_key=config.api_key,
            base_url=config.api_base,
        )
        logger.info(f"OpenAI Embedder initialized with model: {config.model_name_or_path}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for the given texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings.
        """
        # Truncate texts if needed
        texts = self._truncate_texts(texts, self.config.max_tokens)

        # Handle empty input
        if not texts:
            return []

        # Build request parameters
        params = {
            "model": self.config.model_name_or_path,
            "input": texts,
        }

        # Add dimensions if specified and model supports it
        if self.config.embedding_dims is not None:
            params["dimensions"] = self.config.embedding_dims

        response = self.client.embeddings.create(**params)

        # Sort by index to ensure correct order
        embeddings_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in embeddings_data]
