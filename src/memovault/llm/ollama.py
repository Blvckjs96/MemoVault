"""Ollama LLM implementation for MemoVault."""

from collections.abc import Generator

from ollama import Client

from memovault.config.llm import OllamaLLMConfig
from memovault.llm.base import BaseLLM
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class OllamaLLM(BaseLLM):
    """Ollama LLM implementation."""

    def __init__(self, config: OllamaLLMConfig):
        """Initialize the Ollama LLM.

        Args:
            config: Ollama LLM configuration.
        """
        self.config = config
        self.client = Client(host=config.api_base)

        # Default model if not specified
        if not self.config.model_name_or_path:
            self.config.model_name_or_path = "llama3.1:latest"

        # Ensure the model exists locally
        self._ensure_model_exists()
        logger.info(f"Ollama LLM initialized with model: {config.model_name_or_path}")

    def _list_models(self) -> list[str]:
        """List all models available in the Ollama client."""
        local_models = self.client.list()["models"]
        return [model.model for model in local_models]

    def _ensure_model_exists(self):
        """Ensure the specified model exists locally. If not, pull it."""
        try:
            local_models = self._list_models()
            if self.config.model_name_or_path not in local_models:
                logger.warning(
                    f"Model {self.config.model_name_or_path} not found locally. Pulling..."
                )
                self.client.pull(self.config.model_name_or_path)
        except Exception as e:
            logger.warning(f"Could not verify model existence: {e}")

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Generate a response from Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional generation parameters.

        Returns:
            The generated response text.
        """
        response = self.client.chat(
            model=self.config.model_name_or_path,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
            },
        )
        return response.message.content

    def generate_stream(
        self, messages: list[dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """Generate a streaming response from Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional generation parameters.

        Yields:
            Chunks of the generated response text.
        """
        response = self.client.chat(
            model=self.config.model_name_or_path,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
            },
            stream=True,
        )

        for chunk in response:
            if hasattr(chunk.message, "content") and chunk.message.content:
                yield chunk.message.content
