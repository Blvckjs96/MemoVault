"""Environment-based settings for MemoVault."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MemoVault settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MEMOVAULT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings
    llm_backend: Literal["openai", "ollama"] = Field(default="openai")
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_api_base: str = Field(default="https://api.openai.com/v1")
    ollama_model: str = Field(default="llama3.1:latest")
    ollama_api_base: str = Field(default="http://localhost:11434")
    llm_temperature: float = Field(default=0.7)
    llm_max_tokens: int = Field(default=4096)

    # Embedder Settings
    embedder_backend: Literal["openai", "ollama", "sentence_transformer"] = Field(
        default="openai"
    )
    embedder_openai_model: str = Field(default="text-embedding-3-small")
    embedder_openai_dims: int = Field(default=1536)
    embedder_ollama_model: str = Field(default="nomic-embed-text:latest")
    embedder_st_model: str = Field(default="all-MiniLM-L6-v2")

    # Memory Settings
    memory_backend: Literal["vector", "simple"] = Field(default="vector")

    # Qdrant Settings
    qdrant_mode: Literal["local", "server"] = Field(default="local")
    qdrant_path: str = Field(default="./memovault_data/qdrant")
    qdrant_host: str | None = Field(default=None)
    qdrant_port: int | None = Field(default=None)
    qdrant_url: str | None = Field(default=None)
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection: str = Field(default="memovault_memories")
    qdrant_vector_dim: int = Field(default=1536)

    # Storage Settings
    data_dir: str = Field(default="./memovault_data")

    # API Settings
    # Bind to localhost by default — prevents network-accessible exposure.
    # Set MEMOVAULT_API_HOST=0.0.0.0 explicitly to expose on the network.
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8080)

    # Intelligence Layer
    auto_score: bool = Field(default=True)
    importance_threshold: int = Field(default=5)
    scorer_ollama_model: str = Field(default="")
    scorer_openai_model: str = Field(default="")

    # STM/LTM Settings
    ltm_base_threshold: float = Field(
        default=2.0, description="Base threshold for LTM candidate admission"
    )
    ltm_max_capacity: int = Field(
        default=10000, description="Max LTM capacity for memory pressure calculation"
    )
    stm_enabled: bool = Field(
        default=True, description="Enable short-term memory"
    )
    promotion_recall_threshold: int = Field(
        default=3, description="Recall count required to promote candidate to LTM"
    )

    # Logging
    log_level: str = Field(default="INFO")

    def validate_credentials(self) -> None:
        """Raise ValueError if required credentials are missing for the chosen backend."""
        if self.llm_backend == "openai" and not self.openai_api_key:
            raise ValueError(
                "MEMOVAULT_OPENAI_API_KEY must be set when MEMOVAULT_LLM_BACKEND=openai. "
                "Add it to your .env file or environment."
            )

    @property
    def data_path(self) -> Path:
        """Get the data directory as a Path object."""
        path = Path(self.data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def qdrant_data_path(self) -> Path:
        """Get the Qdrant data directory as a Path object."""
        path = Path(self.qdrant_path)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
