"""Embedder configuration classes."""

from typing import Any, Literal

from pydantic import Field

from memovault.config.base import BaseConfig


class BaseEmbedderConfig(BaseConfig):
    """Base configuration class for embedding models."""

    model_name_or_path: str = Field(..., description="Model name or path")
    embedding_dims: int | None = Field(
        default=None, description="Number of dimensions for the embedding"
    )
    max_tokens: int | None = Field(
        default=8192,
        description="Maximum number of tokens per text. Texts exceeding this limit will be truncated.",
    )


class OpenAIEmbedderConfig(BaseEmbedderConfig):
    """OpenAI Embedder configuration."""

    api_key: str = Field(..., description="API key for OpenAI")
    api_base: str = Field(
        default="https://api.openai.com/v1", description="Base URL for OpenAI API"
    )


class OllamaEmbedderConfig(BaseEmbedderConfig):
    """Ollama Embedder configuration."""

    api_base: str = Field(
        default="http://localhost:11434", description="Base URL for Ollama API"
    )


class SentenceTransformerConfig(BaseEmbedderConfig):
    """Sentence Transformer Embedder configuration."""

    trust_remote_code: bool = Field(
        default=True,
        description="Whether to trust remote code when loading the model",
    )


class EmbedderConfig(BaseConfig):
    """Factory configuration for Embedders."""

    backend: Literal["openai", "ollama", "sentence_transformer"] = Field(
        ..., description="Embedder backend"
    )
    config: OpenAIEmbedderConfig | OllamaEmbedderConfig | SentenceTransformerConfig = Field(
        ..., description="Backend configuration"
    )

    @classmethod
    def from_settings(cls, settings: Any) -> "EmbedderConfig":
        """Create Embedder config from settings."""
        if settings.embedder_backend == "openai":
            config = OpenAIEmbedderConfig(
                model_name_or_path=settings.embedder_openai_model,
                api_key=settings.openai_api_key,
                api_base=settings.openai_api_base,
                embedding_dims=settings.embedder_openai_dims,
            )
        elif settings.embedder_backend == "ollama":
            config = OllamaEmbedderConfig(
                model_name_or_path=settings.embedder_ollama_model,
                api_base=settings.ollama_api_base,
            )
        else:  # sentence_transformer
            config = SentenceTransformerConfig(
                model_name_or_path=settings.embedder_st_model,
            )
        return cls(backend=settings.embedder_backend, config=config)
