"""API request/response models for MemoVault."""

from pydantic import BaseModel, Field


class AddMemoryRequest(BaseModel):
    """Request to add a memory."""

    content: str = Field(..., description="Memory content to add")
    type: str | None = Field(default=None, description="Memory type")
    tags: list[str] | None = Field(default=None, description="Memory tags")


class SearchRequest(BaseModel):
    """Request to search memories."""

    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, description="Number of results to return")


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
