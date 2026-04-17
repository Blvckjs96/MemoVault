"""REST API for MemoVault using FastAPI."""

import os
import uuid as _uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from memovault.api.models import (
    AddMemoryRequest,
    ChatRequest,
    ChatResponse,
    ConsolidateRequest,
    ConsolidateResponse,
    MemoryResponse,
    ProfileUpdateRequest,
    SearchRequest,
    SearchResponse,
    SessionContextResponse,
    SessionStartRequest,
    SessionResponse,
    STMItemResponse,
    StatsResponse,
    StatusResponse,
    TokenStatsResponse,
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

    # CORS — restrict to localhost origins only.
    # The dashboard is served same-origin so it needs no CORS at all.
    # allow_credentials must be False when allow_origins is not ["*"];
    # combining wildcard + credentials is rejected by browsers and opens
    # a cross-origin data-theft vector.
    _raw = os.environ.get("MEMOVAULT_ALLOWED_ORIGINS", "")
    allowed_origins = (
        [o.strip() for o in _raw.split(",") if o.strip()]
        if _raw
        else [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    # Global exception handler — never leak internal details to clients
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Initialize MemoVault
    if memovault is None:
        vault = MemoVault()
    else:
        vault = memovault

    # =========================================================================
    # Status
    # =========================================================================

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

    @app.get("/stats", response_model=StatsResponse, tags=["Status"])
    async def stats():
        """Get dashboard statistics."""
        try:
            all_memories = vault.get_all()
            type_counts: dict[str, int] = {}
            for mem in all_memories:
                t = mem.metadata.type or "untyped"
                type_counts[t] = type_counts.get(t, 0) + 1

            scorer_model = (
                vault.settings.scorer_ollama_model
                or vault.settings.scorer_openai_model
                or None
            )

            # Count LTM statuses
            ltm_candidates = sum(
                1 for m in all_memories if getattr(m.metadata, "ltm_status", None) == "candidate"
            )
            ltm_promoted = sum(
                1 for m in all_memories if getattr(m.metadata, "ltm_status", None) == "promoted"
            )
            stm_count = vault.stm.count() if vault.stm else 0

            return StatsResponse(
                status="active",
                memory_count=len(all_memories),
                auto_score=vault.settings.auto_score,
                importance_threshold=vault.settings.importance_threshold,
                backend=vault._memory_config.backend,
                profile=vault.get_profile(),
                memory_types=type_counts,
                scorer_model=scorer_model,
                stm_count=stm_count,
                ltm_candidate_count=ltm_candidates,
                ltm_promoted_count=ltm_promoted,
            )
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/stats/tokens", response_model=TokenStatsResponse, tags=["Status"])
    async def token_stats():
        """Get token economics for the current server session."""
        return TokenStatsResponse(**vault.token_stats())

    @app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard():
        """Serve the MemoVault dashboard UI."""
        ui_path = Path(__file__).parent.parent / "ui" / "dashboard.html"
        if not ui_path.exists():
            raise HTTPException(status_code=404, detail="Dashboard not found")
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none';"
        )
        return HTMLResponse(
            content=ui_path.read_text(encoding="utf-8"),
            headers={"Content-Security-Policy": csp},
        )

    # =========================================================================
    # Memories
    # =========================================================================

    @app.post("/memories", response_model=MemoryResponse, tags=["Memories"])
    async def add_memory(request: AddMemoryRequest):
        """Add a new memory."""
        try:
            metadata: dict[str, Any] = {}
            if request.type:
                metadata["type"] = request.type
            if request.tags:
                metadata["tags"] = request.tags

            ids = vault.add(
                request.content,
                skip_scoring=request.skip_scoring,
                **metadata,
            )
            if not ids:
                raise HTTPException(
                    status_code=422,
                    detail="Memory was not stored (below importance threshold)",
                )

            memory = vault.get(ids[0])
            if memory:
                return MemoryResponse(
                    id=memory.id,
                    memory=memory.memory,
                    type=memory.metadata.type,
                    created_at=memory.metadata.created_at,
                    ltm_status=getattr(memory.metadata, "ltm_status", None),
                    recall_count=getattr(memory.metadata, "recall_count", None),
                    final_score=getattr(memory.metadata, "final_score", None),
                )
            raise HTTPException(status_code=500, detail="Failed to retrieve added memory")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memories/search", response_model=SearchResponse, tags=["Memories"])
    async def search_memories(request: SearchRequest):
        """Search for memories."""
        try:
            kwargs: dict[str, Any] = {}
            filter_dict: dict[str, Any] = {}
            if request.memory_type:
                filter_dict["metadata.type"] = request.memory_type
            if request.source:
                filter_dict["metadata.source"] = request.source
            if filter_dict:
                kwargs["filter"] = filter_dict

            results = vault.search(request.query, request.top_k, max_age_days=request.max_age_days, **kwargs)
            return SearchResponse(
                memories=[
                    MemoryResponse(
                        id=mem.id,
                        memory=mem.memory,
                        type=mem.metadata.type,
                        created_at=mem.metadata.created_at,
                        ltm_status=getattr(mem.metadata, "ltm_status", None),
                        recall_count=getattr(mem.metadata, "recall_count", None),
                        final_score=getattr(mem.metadata, "final_score", None),
                    )
                    for mem in results
                ],
                total=len(results),
            )
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def _validate_memory_id(memory_id: str) -> None:
        try:
            _uuid.UUID(memory_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid memory ID format")

    @app.get("/memories/{memory_id}", response_model=MemoryResponse, tags=["Memories"])
    async def get_memory(memory_id: str):
        """Get a specific memory by ID."""
        _validate_memory_id(memory_id)
        memory = vault.get(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")

        return MemoryResponse(
            id=memory.id,
            memory=memory.memory,
            type=memory.metadata.type,
            created_at=memory.metadata.created_at,
            ltm_status=getattr(memory.metadata, "ltm_status", None),
            recall_count=getattr(memory.metadata, "recall_count", None),
            final_score=getattr(memory.metadata, "final_score", None),
        )

    @app.delete("/memories/{memory_id}", tags=["Memories"])
    async def delete_memory(memory_id: str):
        """Delete a specific memory."""
        try:
            _validate_memory_id(memory_id)
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
    async def list_memories(limit: int = Query(default=50, ge=1, le=500)):
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
                        ltm_status=getattr(mem.metadata, "ltm_status", None),
                        recall_count=getattr(mem.metadata, "recall_count", None),
                        final_score=getattr(mem.metadata, "final_score", None),
                    )
                    for mem in recent
                ],
                "total": len(all_memories),
                "returned": len(recent),
            }
        except Exception as e:
            logger.error(f"Error listing memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memories/consolidate", response_model=ConsolidateResponse, tags=["Memories"])
    async def consolidate_memories(request: ConsolidateRequest | None = None):
        """Consolidate near-duplicate memories."""
        try:
            threshold = request.threshold if request else 0.85
            result = vault.consolidate_memories(similarity_threshold=threshold)
            return ConsolidateResponse(
                status="completed",
                merged_groups=result["merged_groups"],
                total_removed=result["total_removed"],
            )
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # =========================================================================
    # STM (Short-Term Memory)
    # =========================================================================

    @app.get("/stm", tags=["STM"])
    async def list_stm():
        """List active STM items."""
        if vault.stm is None:
            return {"items": [], "total": 0, "message": "STM is disabled"}
        items = vault.stm.get_active()
        return {
            "items": [
                STMItemResponse(
                    id=item.id,
                    content=item.content,
                    utility_score=item.utility_score,
                    decay_turns=item.decay_turns,
                    category=item.category,
                    created_turn=item.created_turn,
                    created_at=item.created_at,
                )
                for item in items
            ],
            "total": len(items),
        }

    @app.delete("/stm", tags=["STM"])
    async def clear_stm():
        """Clear all STM items."""
        if vault.stm is None:
            return {"message": "STM is disabled"}
        vault.stm.clear()
        return {"message": "STM cleared"}

    # =========================================================================
    # LTM Lifecycle
    # =========================================================================

    @app.get("/memories/candidates", tags=["LTM Lifecycle"])
    async def list_candidates(limit: int = 50):
        """List LTM candidate memories."""
        try:
            all_memories = vault.get_all()
            candidates = [
                m for m in all_memories
                if getattr(m.metadata, "ltm_status", None) == "candidate"
            ]
            recent = candidates[-limit:] if len(candidates) > limit else candidates
            recent.reverse()
            return {
                "memories": [
                    MemoryResponse(
                        id=mem.id,
                        memory=mem.memory,
                        type=mem.metadata.type,
                        created_at=mem.metadata.created_at,
                        ltm_status=mem.metadata.ltm_status,
                        recall_count=getattr(mem.metadata, "recall_count", 0),
                        final_score=getattr(mem.metadata, "final_score", None),
                    )
                    for mem in recent
                ],
                "total": len(candidates),
            }
        except Exception as e:
            logger.error(f"Error listing candidates: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/memories/promoted", tags=["LTM Lifecycle"])
    async def list_promoted(limit: int = 50):
        """List promoted LTM memories."""
        try:
            all_memories = vault.get_all()
            promoted = [
                m for m in all_memories
                if getattr(m.metadata, "ltm_status", None) == "promoted"
                or getattr(m.metadata, "ltm_status", None) is None
            ]
            recent = promoted[-limit:] if len(promoted) > limit else promoted
            recent.reverse()
            return {
                "memories": [
                    MemoryResponse(
                        id=mem.id,
                        memory=mem.memory,
                        type=mem.metadata.type,
                        created_at=mem.metadata.created_at,
                        ltm_status=getattr(mem.metadata, "ltm_status", None),
                        recall_count=getattr(mem.metadata, "recall_count", 0),
                        final_score=getattr(mem.metadata, "final_score", None),
                    )
                    for mem in recent
                ],
                "total": len(promoted),
            }
        except Exception as e:
            logger.error(f"Error listing promoted: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memories/{memory_id}/promote", tags=["LTM Lifecycle"])
    async def promote_memory(memory_id: str):
        """Manually promote a candidate memory to promoted status."""
        try:
            memory = vault.get(memory_id)
            if memory is None:
                raise HTTPException(status_code=404, detail="Memory not found")

            memory.metadata.ltm_status = "promoted"
            vault._cube.update(memory)
            return {"message": f"Memory {memory_id} promoted", "ltm_status": "promoted"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error promoting memory: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # =========================================================================
    # Chat
    # =========================================================================

    @app.post("/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat(request: ChatRequest):
        """Chat with memory-enhanced responses."""
        try:
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

    # =========================================================================
    # Profile
    # =========================================================================

    @app.get("/profile", tags=["Profile"])
    async def get_profile():
        """Get user profile."""
        try:
            return vault.get_profile()
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/profile/{field}", tags=["Profile"])
    async def update_profile(field: str, request: ProfileUpdateRequest):
        """Update a profile field."""
        try:
            vault.update_profile(field, request.value)
            return {"message": f"Profile field '{field}' updated", "field": field}
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # =========================================================================
    # Sessions
    # =========================================================================

    @app.get("/session/context", response_model=SessionContextResponse, tags=["Sessions"])
    async def get_session_context(
        query: str | None = Query(default=None, max_length=4096, description="Prompt to find relevant facts"),
        top_k: int = Query(default=5, ge=1, le=20),
    ):
        """Return recent session summaries + relevant facts for context continuity.

        Designed for the UserPromptSubmit hook so every new prompt gets
        both prior-session recaps and query-relevant memories.
        """
        try:
            ctx = vault.get_session_context(query=query, top_k=top_k)
            return SessionContextResponse(
                recap=ctx["recap"],
                relevant_facts=ctx["relevant_facts"],
                profile=ctx["profile"],
            )
        except Exception as e:
            logger.error(f"Error fetching session context: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/session/start", tags=["Sessions"])
    async def start_session(request: SessionStartRequest | None = None):
        """Start a new session with context loading."""
        try:
            first_message = request.first_message if request else None
            context = vault.get_session_context(query=first_message, top_k=5)
            return {
                "profile": context["profile"],
                "recap": context["recap"],
                "relevant_facts": context["relevant_facts"],
            }
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/session/end", response_model=SessionResponse, tags=["Sessions"])
    async def end_session():
        """End current session with summary."""
        try:
            summary = vault.end_session()
            if summary:
                return SessionResponse(
                    summary=summary,
                    message="Session ended and summary stored",
                )
            return SessionResponse(
                summary=None,
                message="No chat history to summarize",
            )
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app


def run_server(host: str = "127.0.0.1", port: int = 8080):
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
