"""Embedder factory for MemoVault."""

from memovault.config.embedder import (
    EmbedderConfig,
    OllamaEmbedderConfig,
    OpenAIEmbedderConfig,
    SentenceTransformerConfig,
)
from memovault.embedder.base import BaseEmbedder
from memovault.embedder.ollama import OllamaEmbedder
from memovault.embedder.openai import OpenAIEmbedder
from memovault.embedder.sentence_transformer import SentenceTransformerEmbedder


class EmbedderFactory:
    """Factory class for creating Embedder instances."""

    @staticmethod
    def from_config(config: EmbedderConfig) -> BaseEmbedder:
        """Create an Embedder instance from configuration.

        Args:
            config: Embedder factory configuration.

        Returns:
            An Embedder instance.

        Raises:
            ValueError: If the backend is not supported.
        """
        if config.backend == "openai":
            if not isinstance(config.config, OpenAIEmbedderConfig):
                raise ValueError("OpenAI backend requires OpenAIEmbedderConfig")
            return OpenAIEmbedder(config.config)
        elif config.backend == "ollama":
            if not isinstance(config.config, OllamaEmbedderConfig):
                raise ValueError("Ollama backend requires OllamaEmbedderConfig")
            return OllamaEmbedder(config.config)
        elif config.backend == "sentence_transformer":
            if not isinstance(config.config, SentenceTransformerConfig):
                raise ValueError(
                    "Sentence Transformer backend requires SentenceTransformerConfig"
                )
            return SentenceTransformerEmbedder(config.config)
        else:
            raise ValueError(f"Unsupported embedder backend: {config.backend}")
