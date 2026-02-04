"""OpenAI LLM implementation for MemoVault."""

from collections.abc import Generator

import openai

from memovault.config.llm import OpenAILLMConfig
from memovault.llm.base import BaseLLM
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation using openai.chat.completions.create."""

    def __init__(self, config: OpenAILLMConfig):
        """Initialize the OpenAI LLM.

        Args:
            config: OpenAI LLM configuration.
        """
        self.config = config
        self.client = openai.Client(
            api_key=config.api_key,
            base_url=config.api_base,
        )
        logger.info(f"OpenAI LLM initialized with model: {config.model_name_or_path}")

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Generate a response from OpenAI.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional generation parameters.

        Returns:
            The generated response text.
        """
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.config.model_name_or_path),
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            top_p=kwargs.get("top_p", self.config.top_p),
        )

        if not response.choices:
            logger.warning("OpenAI response has no choices")
            return ""

        content = response.choices[0].message.content
        return content or ""

    def generate_stream(
        self, messages: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """Generate a streaming response from OpenAI.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional generation parameters.

        Yields:
            Chunks of the generated response text.
        """
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.config.model_name_or_path),
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            top_p=kwargs.get("top_p", self.config.top_p),
            stream=True,
        )

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content
