"""Memory factory for MemoVault."""

from memovault.config.memory import MemoryConfig, SimpleMemoryConfig, VectorMemoryConfig
from memovault.memory.base import BaseTextMemory
from memovault.memory.simple import SimpleMemory
from memovault.memory.vector import VectorMemory


class MemoryFactory:
    """Factory class for creating Memory instances."""

    @staticmethod
    def from_config(config: MemoryConfig) -> BaseTextMemory:
        """Create a Memory instance from configuration.

        Args:
            config: Memory factory configuration.

        Returns:
            A Memory instance.

        Raises:
            ValueError: If the backend is not supported.
        """
        if config.backend == "simple":
            if not isinstance(config.config, SimpleMemoryConfig):
                raise ValueError("Simple backend requires SimpleMemoryConfig")
            return SimpleMemory(config.config)
        elif config.backend == "vector":
            if not isinstance(config.config, VectorMemoryConfig):
                raise ValueError("Vector backend requires VectorMemoryConfig")
            return VectorMemory(config.config)
        else:
            raise ValueError(f"Unsupported memory backend: {config.backend}")
