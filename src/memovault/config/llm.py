"""LLM configuration classes."""

from typing import Any, Literal

from pydantic import Field

from memovault.config.base import BaseConfig


class BaseLLMConfig(BaseConfig):
    """Base configuration class for LLMs."""

    model_name_or_path: str = Field(..., description="Model name or path")
    temperature: float = Field(default=0.7, description="Temperature for sampling")
    max_tokens: int = Field(default=4096, description="Maximum number of tokens to generate")
    top_p: float = Field(default=0.95, description="Top-p sampling parameter")


class OpenAILLMConfig(BaseLLMConfig):
    """OpenAI LLM configuration."""

    api_key: str = Field(..., description="API key for OpenAI")
    api_base: str = Field(
        default="https://api.openai.com/v1", description="Base URL for OpenAI API"
    )


class OllamaLLMConfig(BaseLLMConfig):
    """Ollama LLM configuration."""

    api_base: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API",
    )


class LLMConfig(BaseConfig):
    """Factory configuration for LLMs."""

    backend: Literal["openai", "ollama"] = Field(..., description="LLM backend")
    config: OpenAILLMConfig | OllamaLLMConfig = Field(..., description="Backend configuration")

    @classmethod
    def from_settings(cls, settings: Any) -> "LLMConfig":
        """Create LLM config from settings."""
        if settings.llm_backend == "openai":
            config = OpenAILLMConfig(
                model_name_or_path=settings.openai_model,
                api_key=settings.openai_api_key,
                api_base=settings.openai_api_base,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        else:  # ollama
            config = OllamaLLMConfig(
                model_name_or_path=settings.ollama_model,
                api_base=settings.ollama_api_base,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        return cls(backend=settings.llm_backend, config=config)

    @classmethod
    def for_scorer(cls, settings: Any) -> "LLMConfig | None":
        """Create a separate LLM config for the scorer (fast model).

        Returns None if no scorer model is configured, meaning the
        main LLM should be used instead.
        """
        if settings.llm_backend == "ollama" and settings.scorer_ollama_model:
            config = OllamaLLMConfig(
                model_name_or_path=settings.scorer_ollama_model,
                api_base=settings.ollama_api_base,
                temperature=0.3,
                max_tokens=512,
            )
            return cls(backend="ollama", config=config)
        elif settings.llm_backend == "openai" and settings.scorer_openai_model:
            config = OpenAILLMConfig(
                model_name_or_path=settings.scorer_openai_model,
                api_key=settings.openai_api_key,
                api_base=settings.openai_api_base,
                temperature=0.3,
                max_tokens=512,
            )
            return cls(backend="openai", config=config)
        return None
