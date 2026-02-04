"""LLM factory for MemoVault."""

from memovault.config.llm import LLMConfig, OllamaLLMConfig, OpenAILLMConfig
from memovault.llm.base import BaseLLM
from memovault.llm.ollama import OllamaLLM
from memovault.llm.openai import OpenAILLM


class LLMFactory:
    """Factory class for creating LLM instances."""

    @staticmethod
    def from_config(config: LLMConfig) -> BaseLLM:
        """Create an LLM instance from configuration.

        Args:
            config: LLM factory configuration.

        Returns:
            An LLM instance.

        Raises:
            ValueError: If the backend is not supported.
        """
        if config.backend == "openai":
            if not isinstance(config.config, OpenAILLMConfig):
                raise ValueError("OpenAI backend requires OpenAILLMConfig")
            return OpenAILLM(config.config)
        elif config.backend == "ollama":
            if not isinstance(config.config, OllamaLLMConfig):
                raise ValueError("Ollama backend requires OllamaLLMConfig")
            return OllamaLLM(config.config)
        else:
            raise ValueError(f"Unsupported LLM backend: {config.backend}")
