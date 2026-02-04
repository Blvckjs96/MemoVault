"""Base LLM class for MemoVault."""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any


class BaseLLM(ABC):
    """Base class for all LLMs."""

    @abstractmethod
    def __init__(self, config: Any):
        """Initialize the LLM with the given configuration."""

    @abstractmethod
    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional generation parameters.

        Returns:
            The generated response text.
        """

    def generate_stream(
        self, messages: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """Generate a streaming response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional generation parameters.

        Yields:
            Chunks of the generated response text.
        """
        # Default implementation: yield the full response
        yield self.generate(messages, **kwargs)
