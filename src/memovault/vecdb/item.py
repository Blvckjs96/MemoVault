"""Vector database item types for MemoVault."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VecDBItem(BaseModel):
    """Represents a single item in the vector database.

    This serves as a standardized format for vector database items.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    vector: list[float] | None = Field(default=None, description="Embedding vector")
    payload: dict[str, Any] | None = Field(
        default=None, description="Additional payload for filtering/retrieval"
    )
    score: float | None = Field(
        default=None, description="Similarity score (used in search results)"
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that ID is a valid UUID string."""
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError("ID must be a valid UUID string")
        return v

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VecDBItem":
        """Create VecDBItem from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return self.model_dump(exclude_none=True)
