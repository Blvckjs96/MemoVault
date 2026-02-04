"""Configuration module for MemoVault."""

from memovault.config.base import BaseConfig
from memovault.config.embedder import EmbedderConfig, OpenAIEmbedderConfig, OllamaEmbedderConfig
from memovault.config.llm import LLMConfig, OpenAILLMConfig, OllamaLLMConfig
from memovault.config.memory import MemoryConfig, SimpleMemoryConfig, VectorMemoryConfig
from memovault.config.settings import Settings, get_settings
from memovault.config.vecdb import QdrantConfig

__all__ = [
    "BaseConfig",
    "EmbedderConfig",
    "OpenAIEmbedderConfig",
    "OllamaEmbedderConfig",
    "LLMConfig",
    "OpenAILLMConfig",
    "OllamaLLMConfig",
    "MemoryConfig",
    "SimpleMemoryConfig",
    "VectorMemoryConfig",
    "QdrantConfig",
    "Settings",
    "get_settings",
]
