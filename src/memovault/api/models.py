"""API request/response models for MemoVault."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AddMemoryRequest(BaseModel):
    """Request to add a memory."""

    content: str = Field(..., description="Memory content to add")
    type: str | None = Field(default=None, description="Memory type")
    tags: list[str] | None = Field(default=None, description="Memory tags")
    skip_scoring: bool = Field(default=False, description="Bypass importance scoring")


class SearchRequest(BaseModel):
    """Request to search memories."""

    query: str = Field(..., min_length=1, max_length=4096, description="Search query")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    memory_type: str | None = Field(default=None, description="Filter by memory type")
    source: str | None = Field(default=None, description="Filter by source")
    max_age_days: int | None = Field(default=None, ge=1, le=36500, description="Exclude memories older than N days")


class ChatRequest(BaseModel):
    """Request for memory-enhanced chat."""

    query: str = Field(..., description="User query")
    top_k: int = Field(default=5, description="Number of memories to use as context")
    include_history: bool = Field(default=True, description="Include chat history")


class MemoryResponse(BaseModel):
    """Response containing a memory."""

    id: str = Field(..., description="Memory ID")
    memory: str = Field(..., description="Memory content")
    type: str | None = Field(default=None, description="Memory type")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    ltm_status: str | None = Field(default=None, description="LTM lifecycle status")
    recall_count: int | None = Field(default=None, description="Times recalled in search")
    final_score: float | None = Field(default=None, description="LTM final score")


class SearchResponse(BaseModel):
    """Response containing search results."""

    memories: list[MemoryResponse] = Field(..., description="List of matching memories")
    total: int = Field(..., description="Total number of results")


class ChatResponse(BaseModel):
    """Response from chat."""

    response: str = Field(..., description="Assistant response")
    memories_used: int = Field(..., description="Number of memories used as context")


class StatusResponse(BaseModel):
    """Status response."""

    status: str = Field(..., description="Status message")
    memory_count: int = Field(..., description="Total number of memories")


# Intelligence Layer Models

class ProfileUpdateRequest(BaseModel):
    """Request to update a profile field."""

    value: str | int | float | bool | list[str] | dict[str, str] = Field(
        ..., description="New value for the field"
    )

    @field_validator("value")
    @classmethod
    def _bound_size(cls, v: Any) -> Any:
        if len(str(v)) > 4096:
            raise ValueError("value exceeds maximum allowed size (4096 chars)")
        return v


class SessionContextResponse(BaseModel):
    """Rich context for session continuity."""

    recap: list[str] = Field(default_factory=list, description="Recent session summaries (last 3)")
    relevant_facts: list[str] = Field(default_factory=list, description="Facts relevant to the query")
    profile: str = Field(default="", description="User profile summary")


class SessionStartRequest(BaseModel):
    """Request to start a session."""

    first_message: str | None = Field(default=None, description="Optional first message for context")


class SessionResponse(BaseModel):
    """Response from session operations."""

    summary: str | None = Field(default=None, description="Session summary")
    message: str = Field(..., description="Status message")


class ConsolidateRequest(BaseModel):
    """Request to consolidate memories."""

    threshold: float = Field(default=0.85, description="Similarity threshold (0.0-1.0)")


class ConsolidateResponse(BaseModel):
    """Response from memory consolidation."""

    status: str = Field(..., description="Consolidation status")
    merged_groups: int = Field(..., description="Number of groups merged")
    total_removed: int = Field(..., description="Net memories removed")


class STMItemResponse(BaseModel):
    """Response containing an STM item."""

    id: str = Field(..., description="STM item ID")
    content: str = Field(..., description="Memory content")
    utility_score: int = Field(..., description="Utility score (0-3)")
    decay_turns: int = Field(..., description="Turns until eviction")
    category: str = Field(..., description="STM category")
    created_turn: int = Field(..., description="Turn when created")
    created_at: str = Field(..., description="Creation timestamp")


class TokenStatsResponse(BaseModel):
    """Token economics for the current session."""

    discovery_tokens: int = Field(..., description="Estimated tokens spent on search queries")
    read_tokens: int = Field(..., description="Estimated tokens injected as context")
    efficiency: float = Field(..., description="read_tokens / discovery_tokens (>1 = net positive)")


class StatsResponse(BaseModel):
    """Dashboard statistics response."""

    status: str = Field(..., description="System status")
    memory_count: int = Field(..., description="Total memories")
    auto_score: bool = Field(..., description="Whether auto-scoring is enabled")
    importance_threshold: int = Field(..., description="Minimum importance score")
    backend: str = Field(..., description="Memory backend type")
    profile: dict[str, Any] = Field(default_factory=dict, description="User profile summary")
    memory_types: dict[str, int] = Field(default_factory=dict, description="Memory count by type")
    scorer_model: str | None = Field(default=None, description="Fast model used for scoring")
    stm_count: int = Field(default=0, description="Active STM items")
    ltm_candidate_count: int = Field(default=0, description="LTM candidate memories")
    ltm_promoted_count: int = Field(default=0, description="Promoted LTM memories")
