"""Memory item types for MemoVault."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryMetadata(BaseModel):
    """Metadata for a memory item."""

    type: str | None = Field(
        default=None,
        description="Type of memory: fact, preference, event, opinion, procedure, personal",
    )
    source: Literal["conversation", "manual", "document", "system"] | None = Field(
        default="conversation", description="Origin of the memory"
    )
    tags: list[str] | None = Field(
        default=None, description="Tags for categorization"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Creation timestamp",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Last update timestamp",
    )

    model_config = ConfigDict(extra="allow")

    def __str__(self) -> str:
        """String representation of metadata."""
        meta = self.model_dump(exclude_none=True)
        return ", ".join(f"{k}={v}" for k, v in meta.items())


class MemoryItem(BaseModel):
    """Represents a single memory item."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    memory: str = Field(..., description="The memory content")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)

    model_config = ConfigDict(extra="forbid")

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str) -> str:
        """Validate UUID format."""
        uuid.UUID(v)
        return v

    @field_validator("metadata", mode="before")
    @classmethod
    def _coerce_metadata(cls, v: Any) -> Any:
        """Coerce metadata from dict if needed."""
        if isinstance(v, MemoryMetadata):
            return v
        if isinstance(v, dict):
            # Remove top-level fields that belong to MemoryItem
            v = v.copy()
            v.pop("id", None)
            v.pop("memory", None)
            return MemoryMetadata(**v)
        return v

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        """Create from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump(exclude_none=True)

    def __str__(self) -> str:
        """String representation."""
        return f"<ID: {self.id} | Memory: {self.memory} | {self.metadata}>"
