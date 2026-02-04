"""Memory configuration classes."""

from typing import Any, Literal

from pydantic import Field

from memovault.config.base import BaseConfig
from memovault.config.embedder import EmbedderConfig
from memovault.config.llm import LLMConfig
from memovault.config.vecdb import QdrantConfig


class BaseMemoryConfig(BaseConfig):
    """Base configuration class for memories."""

    memory_filename: str = Field(
        default="memories.json",
        description="Filename for storing memories",
    )


class SimpleMemoryConfig(BaseMemoryConfig):
    """Simple JSON-based memory configuration."""

    extractor_llm: LLMConfig | None = Field(
        default=None,
        description="LLM configuration for memory extraction (optional)",
    )


class VectorMemoryConfig(BaseMemoryConfig):
    """Vector-based memory configuration."""

    extractor_llm: LLMConfig | None = Field(
        default=None,
        description="LLM configuration for memory extraction (optional)",
    )
    vector_db: QdrantConfig = Field(
        ...,
        description="Vector database configuration",
    )
    embedder: EmbedderConfig = Field(
        ...,
        description="Embedder configuration",
    )


class MemoryConfig(BaseConfig):
    """Factory configuration for memories."""

    backend: Literal["simple", "vector"] = Field(..., description="Memory backend")
    config: SimpleMemoryConfig | VectorMemoryConfig = Field(
        ..., description="Backend configuration"
    )

    @classmethod
    def from_settings(cls, settings: Any) -> "MemoryConfig":
        """Create Memory config from settings."""
        if settings.memory_backend == "simple":
            config = SimpleMemoryConfig(
                extractor_llm=LLMConfig.from_settings(settings),
            )
        else:  # vector
            config = VectorMemoryConfig(
                extractor_llm=LLMConfig.from_settings(settings),
                vector_db=QdrantConfig.from_settings(settings),
                embedder=EmbedderConfig.from_settings(settings),
            )
        return cls(backend=settings.memory_backend, config=config)
