"""Qdrant vector database implementation for MemoVault."""

from typing import Any

from memovault.config.vecdb import QdrantConfig
from memovault.utils.log import get_logger
from memovault.vecdb.base import BaseVecDB
from memovault.vecdb.item import VecDBItem

logger = get_logger(__name__)


class QdrantVecDB(BaseVecDB):
    """Qdrant vector database implementation."""

    def __init__(self, config: QdrantConfig):
        """Initialize the Qdrant vector database.

        Args:
            config: Qdrant configuration.
        """
        from qdrant_client import QdrantClient

        self.config = config

        # Build client kwargs based on configuration
        client_kwargs: dict[str, Any] = {}
        if config.url:
            client_kwargs["url"] = config.url
            if config.api_key:
                client_kwargs["api_key"] = config.api_key
        elif config.host and config.port:
            client_kwargs["host"] = config.host
            client_kwargs["port"] = config.port
        else:
            # Local/embedded mode
            client_kwargs["path"] = config.path
            logger.info(f"Qdrant running in local mode at: {config.path}")

        self.client = QdrantClient(**client_kwargs)
        self.create_collection()
        logger.info(f"Qdrant initialized with collection: {config.collection_name}")

    def create_collection(self) -> None:
        """Create a new collection if it doesn't exist."""
        from qdrant_client.http import models
        from qdrant_client.http.exceptions import UnexpectedResponse

        if self.collection_exists(self.config.collection_name):
            logger.debug(f"Collection '{self.config.collection_name}' already exists")
            return

        distance_map = {
            "cosine": models.Distance.COSINE,
            "euclidean": models.Distance.EUCLID,
            "dot": models.Distance.DOT,
        }

        try:
            self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=models.VectorParams(
                    size=self.config.vector_dimension,
                    distance=distance_map[self.config.distance_metric],
                ),
            )
            logger.info(
                f"Created collection '{self.config.collection_name}' "
                f"with {self.config.vector_dimension} dimensions"
            )
        except UnexpectedResponse as err:
            if getattr(err, "status_code", None) == 409 or "already exists" in str(err).lower():
                logger.debug(f"Collection '{self.config.collection_name}' already exists")
                return
            raise

    def list_collections(self) -> list[str]:
        """List all collections."""
        collections = self.client.get_collections()
        return [collection.name for collection in collections.collections]

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        self.client.delete_collection(collection_name=name)
        logger.info(f"Deleted collection: {name}")

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        try:
            self.client.get_collection(collection_name=name)
            return True
        except Exception:
            return False

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filter: dict[str, Any] | None = None,
    ) -> list[VecDBItem]:
        """Search for similar items.

        Args:
            query_vector: Vector to search for.
            top_k: Number of results to return.
            filter: Optional payload filters.

        Returns:
            List of search results with similarity scores.
        """
        qdrant_filter = self._dict_to_filter(filter) if filter else None

        response = self.client.query_points(
            collection_name=self.config.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_vectors=True,
            with_payload=True,
        ).points

        return [
            VecDBItem(
                id=point.id,
                vector=point.vector,
                payload=point.payload,
                score=point.score,
            )
            for point in response
        ]

    def _dict_to_filter(self, filter_dict: dict[str, Any]) -> Any:
        """Convert a dictionary filter to a Qdrant Filter object."""
        from qdrant_client.http import models

        conditions = []
        for field, value in filter_dict.items():
            conditions.append(
                models.FieldCondition(key=field, match=models.MatchValue(value=value))
            )
        return models.Filter(must=conditions)

    def get_by_id(self, id: str) -> VecDBItem | None:
        """Get an item by ID."""
        response = self.client.retrieve(
            collection_name=self.config.collection_name,
            ids=[id],
            with_payload=True,
            with_vectors=True,
        )

        if not response:
            return None

        point = response[0]
        return VecDBItem(
            id=point.id,
            vector=point.vector,
            payload=point.payload,
        )

    def get_by_ids(self, ids: list[str]) -> list[VecDBItem]:
        """Get multiple items by their IDs."""
        if not ids:
            return []

        response = self.client.retrieve(
            collection_name=self.config.collection_name,
            ids=ids,
            with_payload=True,
            with_vectors=True,
        )

        return [
            VecDBItem(
                id=point.id,
                vector=point.vector,
                payload=point.payload,
            )
            for point in response
        ]

    def get_all(self, scroll_limit: int = 100) -> list[VecDBItem]:
        """Get all items in the collection."""
        all_points = []
        offset = None

        while True:
            points, offset = self.client.scroll(
                collection_name=self.config.collection_name,
                limit=scroll_limit,
                offset=offset,
                with_vectors=True,
                with_payload=True,
            )

            if not points:
                break

            all_points.extend(points)

            if offset is None:
                break

        return [
            VecDBItem(
                id=point.id,
                vector=point.vector,
                payload=point.payload,
            )
            for point in all_points
        ]

    def count(self) -> int:
        """Count items in the collection."""
        response = self.client.count(collection_name=self.config.collection_name)
        return response.count

    def add(self, data: list[VecDBItem]) -> None:
        """Add items to the collection."""
        from qdrant_client.http import models

        if not data:
            return

        points = [
            models.PointStruct(
                id=item.id,
                vector=item.vector,
                payload=item.payload,
            )
            for item in data
        ]

        self.client.upsert(collection_name=self.config.collection_name, points=points)
        logger.debug(f"Added {len(data)} items to collection")

    def update(self, id: str, data: VecDBItem) -> None:
        """Update an item in the collection."""
        from qdrant_client.http import models

        if data.vector:
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=[models.PointStruct(id=id, vector=data.vector, payload=data.payload)],
            )
        else:
            self.client.set_payload(
                collection_name=self.config.collection_name,
                payload=data.payload,
                points=[id],
            )

    def delete(self, ids: list[str]) -> None:
        """Delete items from the collection."""
        from qdrant_client.http import models

        if not ids:
            return

        self.client.delete(
            collection_name=self.config.collection_name,
            points_selector=models.PointIdsList(points=ids),
        )
        logger.debug(f"Deleted {len(ids)} items from collection")

    def delete_all(self) -> None:
        """Delete all items from the collection by recreating it."""
        self.delete_collection(self.config.collection_name)
        self.create_collection()
        logger.info(f"Cleared all items from collection: {self.config.collection_name}")
