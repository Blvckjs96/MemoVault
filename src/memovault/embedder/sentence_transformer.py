"""Sentence Transformer embedder implementation for MemoVault."""

from memovault.config.embedder import SentenceTransformerConfig
from memovault.embedder.base import BaseEmbedder
from memovault.utils.log import get_logger

logger = get_logger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Sentence Transformer embedder implementation for local embeddings."""

    def __init__(self, config: SentenceTransformerConfig):
        """Initialize the Sentence Transformer embedder.

        Args:
            config: Sentence Transformer embedder configuration.
        """
        self.config = config
        self._model = None
        logger.info(
            f"Sentence Transformer Embedder will use model: {config.model_name_or_path}"
        )

    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Install it with: pip install memovault[local]"
                )

            self._model = SentenceTransformer(
                self.config.model_name_or_path,
                trust_remote_code=self.config.trust_remote_code,
            )
            logger.info(f"Loaded Sentence Transformer model: {self.config.model_name_or_path}")
        return self._model

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

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
