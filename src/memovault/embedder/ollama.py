"""Ollama embedder implementation for MemoVault."""

from ollama import Client

from memovault.config.embedder import OllamaEmbedderConfig
from memovault.embedder.base import BaseEmbedder
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class OllamaEmbedder(BaseEmbedder):
    """Ollama embedder implementation."""

    def __init__(self, config: OllamaEmbedderConfig):
        """Initialize the Ollama embedder.

        Args:
            config: Ollama embedder configuration.
        """
        self.config = config
        self.client = Client(host=config.api_base)

        # Default model if not specified
        if not self.config.model_name_or_path:
            self.config.model_name_or_path = "nomic-embed-text:latest"

        # Ensure the model exists locally
        self._ensure_model_exists()
        logger.info(f"Ollama Embedder initialized with model: {config.model_name_or_path}")

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

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for the given texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings.
        """
        # Truncate texts if needed
        texts = self._truncate_texts(texts, self.config.max_tokens)

        # Handle empty input
        if not texts:
            return []

        response = self.client.embed(
            model=self.config.model_name_or_path,
            input=texts,
        )
        return response.embeddings
