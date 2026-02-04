"""REST API for MemoVault using FastAPI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from memovault.api.models import (
    AddMemoryRequest,
    ChatRequest,
    ChatResponse,
    MemoryResponse,
    SearchRequest,
    SearchResponse,
    StatusResponse,
)
from memovault.core.memovault import MemoVault
from memovault.utils.log import get_logger

logger = get_logger(__name__)


def create_app(memovault: MemoVault | None = None) -> FastAPI:
    """Create FastAPI application.

    Args:
        memovault: Optional MemoVault instance. If not provided, creates one.

    Returns:
        FastAPI application instance.
    """
    app = FastAPI(
        title="MemoVault API",
        description="REST API for MemoVault - A personal memory system",
        version="0.1.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize MemoVault
    if memovault is None:
        vault = MemoVault()
    else:
        vault = memovault

    @app.get("/", tags=["Status"])
    async def root():
        """Root endpoint."""
        return {"message": "MemoVault API", "version": "0.1.0"}

    @app.get("/status", response_model=StatusResponse, tags=["Status"])
    async def status():
        """Get system status."""
        return StatusResponse(
            status="active",
            memory_count=vault.count(),
        )

    @app.post("/memories", response_model=MemoryResponse, tags=["Memories"])
    async def add_memory(request: AddMemoryRequest):
        """Add a new memory."""
        try:
            metadata = {}
            if request.type:
                metadata["type"] = request.type
            if request.tags:
                metadata["tags"] = request.tags

            ids = vault.add(request.content, **metadata)
            memory = vault.get(ids[0])

            if memory:
                return MemoryResponse(
                    id=memory.id,
                    memory=memory.memory,
                    type=memory.metadata.type,
                    created_at=memory.metadata.created_at,
                )
            raise HTTPException(status_code=500, detail="Failed to retrieve added memory")
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memories/search", response_model=SearchResponse, tags=["Memories"])
    async def search_memories(request: SearchRequest):
        """Search for memories."""
        try:
            results = vault.search(request.query, request.top_k)
            return SearchResponse(
                memories=[
                    MemoryResponse(
                        id=mem.id,
                        memory=mem.memory,
                        type=mem.metadata.type,
                        created_at=mem.metadata.created_at,
                    )
                    for mem in results
                ],
                total=len(results),
            )
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/memories/{memory_id}", response_model=MemoryResponse, tags=["Memories"])
    async def get_memory(memory_id: str):
        """Get a specific memory by ID."""
        memory = vault.get(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")

        return MemoryResponse(
            id=memory.id,
            memory=memory.memory,
            type=memory.metadata.type,
            created_at=memory.metadata.created_at,
        )

    @app.delete("/memories/{memory_id}", tags=["Memories"])
    async def delete_memory(memory_id: str):
        """Delete a specific memory."""
        try:
            memory = vault.get(memory_id)
            if memory is None:
                raise HTTPException(status_code=404, detail="Memory not found")

            vault.delete(memory_id)
            return {"message": f"Memory {memory_id} deleted"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/memories", tags=["Memories"])
    async def clear_memories():
        """Delete all memories."""
        try:
            count = vault.count()
            vault.delete_all()
            return {"message": f"Deleted {count} memories"}
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/memories", tags=["Memories"])
    async def list_memories(limit: int = 50):
        """List all memories."""
        try:
            all_memories = vault.get_all()
            recent = all_memories[-limit:] if len(all_memories) > limit else all_memories
            recent.reverse()

            return {
                "memories": [
                    MemoryResponse(
                        id=mem.id,
                        memory=mem.memory,
                        type=mem.metadata.type,
                        created_at=mem.metadata.created_at,
                    )
                    for mem in recent
                ],
                "total": len(all_memories),
                "returned": len(recent),
            }
        except Exception as e:
            logger.error(f"Error listing memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat(request: ChatRequest):
        """Chat with memory-enhanced responses."""
        try:
            # Get memory count before chat
            memories = vault.search(request.query, request.top_k)

            response = vault.chat(
                request.query,
                top_k=request.top_k,
                include_history=request.include_history,
            )

            return ChatResponse(
                response=response,
                memories_used=len(memories),
            )
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/chat/clear", tags=["Chat"])
    async def clear_chat_history():
        """Clear chat history."""
        vault.clear_chat_history()
        return {"message": "Chat history cleared"}

    return app


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the REST API server.

    Args:
        host: Host to bind to.
        port: Port to bind to.
    """
    import uvicorn

    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MemoVault REST API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")

    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
