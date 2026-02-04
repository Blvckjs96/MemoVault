"""Vector database configuration classes."""

from typing import Any, Literal

from pydantic import Field

from memovault.config.base import BaseConfig


class QdrantConfig(BaseConfig):
    """Configuration for Qdrant vector database."""

    collection_name: str = Field(..., description="Name of the collection")
    vector_dimension: int = Field(default=1536, description="Dimension of the vectors")
    distance_metric: Literal["cosine", "euclidean", "dot"] = Field(
        default="cosine",
        description="Distance metric for vector similarity calculation",
    )

    # Connection options (mutually exclusive patterns)
    host: str | None = Field(default=None, description="Host for Qdrant server")
    port: int | None = Field(default=None, description="Port for Qdrant server")
    path: str | None = Field(default=None, description="Path for local Qdrant storage")
    url: str | None = Field(default=None, description="Qdrant Cloud/remote endpoint URL")
    api_key: str | None = Field(default=None, description="Qdrant Cloud API key")

    @classmethod
    def from_settings(cls, settings: Any) -> "QdrantConfig":
        """Create Qdrant config from settings."""
        if settings.qdrant_mode == "local":
            return cls(
                collection_name=settings.qdrant_collection,
                vector_dimension=settings.qdrant_vector_dim,
                path=settings.qdrant_path,
            )
        else:  # server mode
            return cls(
                collection_name=settings.qdrant_collection,
                vector_dimension=settings.qdrant_vector_dim,
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
