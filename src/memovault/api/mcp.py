"""MCP Server for Claude Code integration."""

import asyncio
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from memovault.core.memovault import MemoVault
from memovault.utils.log import get_logger

load_dotenv()
logger = get_logger(__name__)


class MemoVaultMCPServer:
    """MCP Server for MemoVault - integrates with Claude Code."""

    def __init__(self, memovault: MemoVault | None = None):
        """Initialize the MCP server.

        Args:
            memovault: Optional MemoVault instance. If not provided, creates lazily.
        """
        self.mcp = FastMCP("MemoVault Memory System")
        self._provided_vault = memovault
        self._vault: MemoVault | None = memovault

        self._setup_tools()
        logger.info("MemoVault MCP Server initialized")

    @property
    def vault(self) -> MemoVault:
        """Lazily initialize MemoVault on first access."""
        if self._vault is None:
            try:
                self._vault = MemoVault()
            except Exception as e:
                logger.error(f"Failed to initialize MemoVault: {e}")
                raise RuntimeError(
                    f"MemoVault backend unavailable: {e}. "
                    "Make sure Ollama and Qdrant are running (docker compose --profile vector up)."
                ) from e
        return self._vault

    def _setup_tools(self):
        """Set up MCP tools."""

        @self.mcp.tool()
        async def add_memory(
            content: str,
            memory_type: str | None = None,
            skip_scoring: bool = False,
        ) -> str:
            """Store new information in memory.

            Use this to remember facts, preferences, events, or any important
            information the user wants to persist across sessions.

            Args:
                content: The information to remember
                memory_type: Optional type (fact, preference, event, opinion, procedure, personal)
                skip_scoring: If True, bypass importance scoring and store directly

            Returns:
                Confirmation message with the memory ID
            """
            try:
                metadata = {}
                if memory_type:
                    metadata["type"] = memory_type

                ids = self.vault.add(content, skip_scoring=skip_scoring, **metadata)
                if ids:
                    return f"Memory stored successfully (ID: {ids[0]})"
                return "Memory was not stored (below importance threshold)"
            except Exception as e:
                logger.error(f"Error adding memory: {e}")
                return f"Error storing memory: {str(e)}"

        @self.mcp.tool()
        async def search_memories(
            query: str,
            top_k: int = 5,
            memory_type: str | None = None,
            source: str | None = None,
        ) -> dict[str, Any]:
            """Search for relevant memories.

            Use this to find stored information related to a topic or question.

            Args:
                query: What to search for
                top_k: Maximum number of results (default: 5)
                memory_type: Optional filter by type (fact, preference, event, etc.)
                source: Optional filter by source (conversation, manual, system)

            Returns:
                Dictionary with matching memories
            """
            try:
                kwargs: dict[str, Any] = {}
                filter_dict: dict[str, Any] = {}
                if memory_type:
                    filter_dict["metadata.type"] = memory_type
                if source:
                    filter_dict["metadata.source"] = source
                if filter_dict:
                    kwargs["filter"] = filter_dict

                results = self.vault.search(query, top_k, **kwargs)
                return {
                    "memories": [
                        {
                            "id": mem.id,
                            "memory": mem.memory,
                            "type": mem.metadata.type,
                        }
                        for mem in results
                    ],
                    "total": len(results),
                }
            except Exception as e:
                logger.error(f"Error searching memories: {e}")
                return {"error": str(e), "memories": [], "total": 0}

        @self.mcp.tool()
        async def chat_with_memory(query: str, top_k: int = 5) -> str:
            """Chat with memory-enhanced responses.

            Use this for questions where stored memories might provide context.
            The response will incorporate relevant memories automatically.

            Args:
                query: User's question or message
                top_k: Number of memories to use as context (default: 5)

            Returns:
                AI response enhanced with relevant memories
            """
            try:
                response = self.vault.chat(query, top_k=top_k)
                return response
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                return f"Error generating response: {str(e)}"

        @self.mcp.tool()
        async def get_memory(memory_id: str) -> dict[str, Any]:
            """Retrieve a specific memory by ID.

            Args:
                memory_id: The unique identifier of the memory

            Returns:
                The memory content and metadata
            """
            try:
                memory = self.vault.get(memory_id)
                if memory:
                    return {
                        "id": memory.id,
                        "memory": memory.memory,
                        "type": memory.metadata.type,
                        "created_at": memory.metadata.created_at,
                    }
                return {"error": "Memory not found"}
            except Exception as e:
                logger.error(f"Error getting memory: {e}")
                return {"error": str(e)}

        @self.mcp.tool()
        async def delete_memory(memory_id: str) -> str:
            """Remove a specific memory.

            Args:
                memory_id: The unique identifier of the memory to delete

            Returns:
                Confirmation message
            """
            try:
                self.vault.delete(memory_id)
                return f"Memory deleted successfully (ID: {memory_id})"
            except Exception as e:
                logger.error(f"Error deleting memory: {e}")
                return f"Error deleting memory: {str(e)}"

        @self.mcp.tool()
        async def list_memories(limit: int = 10) -> dict[str, Any]:
            """Show recent memories.

            Args:
                limit: Maximum number of memories to return (default: 10)

            Returns:
                Dictionary with list of recent memories
            """
            try:
                all_memories = self.vault.get_all()
                # Get most recent (last added)
                recent = all_memories[-limit:] if len(all_memories) > limit else all_memories
                recent.reverse()  # Most recent first

                return {
                    "memories": [
                        {
                            "id": mem.id,
                            "memory": mem.memory[:100] + "..." if len(mem.memory) > 100 else mem.memory,
                            "type": mem.metadata.type,
                        }
                        for mem in recent
                    ],
                    "total_in_vault": len(all_memories),
                    "returned": len(recent),
                }
            except Exception as e:
                logger.error(f"Error listing memories: {e}")
                return {"error": str(e), "memories": [], "total_in_vault": 0}

        @self.mcp.tool()
        async def clear_memories() -> str:
            """Clear all stored memories.

            Warning: This permanently deletes all memories!

            Returns:
                Confirmation message
            """
            try:
                count = self.vault.count()
                self.vault.delete_all()
                return f"All {count} memories have been deleted"
            except Exception as e:
                logger.error(f"Error clearing memories: {e}")
                return f"Error clearing memories: {str(e)}"

        @self.mcp.tool()
        async def memory_status() -> dict[str, Any]:
            """Get the current status of the memory system.

            Returns:
                Dictionary with status information
            """
            try:
                scorer_model = (
                    self.vault.settings.scorer_ollama_model
                    or self.vault.settings.scorer_openai_model
                    or None
                )
                stm_count = self.vault.stm.count() if self.vault.stm else 0
                return {
                    "status": "active",
                    "memory_count": self.vault.count(),
                    "backend": self.vault._memory_config.backend,
                    "auto_score": self.vault.settings.auto_score,
                    "importance_threshold": self.vault.settings.importance_threshold,
                    "scorer_model": scorer_model,
                    "stm_active": stm_count,
                }
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return {"status": "error", "error": str(e)}

        # =====================================================================
        # STM & LTM Lifecycle Tools
        # =====================================================================

        @self.mcp.tool()
        async def list_stm() -> dict[str, Any]:
            """List active short-term memory items.

            Returns current session's STM items that haven't expired.

            Returns:
                Dictionary with STM items and count
            """
            try:
                if self.vault.stm is None:
                    return {"items": [], "total": 0, "message": "STM is disabled"}
                items = self.vault.stm.get_active()
                return {
                    "items": [
                        {
                            "id": item.id,
                            "content": item.content[:100] + "..." if len(item.content) > 100 else item.content,
                            "utility_score": item.utility_score,
                            "category": item.category,
                            "decay_turns": item.decay_turns,
                        }
                        for item in items
                    ],
                    "total": len(items),
                }
            except Exception as e:
                logger.error(f"Error listing STM: {e}")
                return {"error": str(e), "items": [], "total": 0}

        @self.mcp.tool()
        async def memory_lifecycle_stats() -> dict[str, Any]:
            """Get STM/LTM lifecycle statistics.

            Shows counts for active STM items, LTM candidates,
            and promoted LTM memories.

            Returns:
                Dictionary with lifecycle statistics
            """
            try:
                all_memories = self.vault.get_all()
                candidates = sum(
                    1 for m in all_memories
                    if getattr(m.metadata, "ltm_status", None) == "candidate"
                )
                promoted = sum(
                    1 for m in all_memories
                    if getattr(m.metadata, "ltm_status", None) == "promoted"
                )
                legacy = sum(
                    1 for m in all_memories
                    if getattr(m.metadata, "ltm_status", None) is None
                )
                stm_count = self.vault.stm.count() if self.vault.stm else 0

                return {
                    "stm_active": stm_count,
                    "ltm_candidates": candidates,
                    "ltm_promoted": promoted,
                    "ltm_legacy": legacy,
                    "total_ltm": len(all_memories),
                }
            except Exception as e:
                logger.error(f"Error getting lifecycle stats: {e}")
                return {"error": str(e)}

        # =====================================================================
        # Profile Tools
        # =====================================================================

        @self.mcp.tool()
        async def update_profile(field: str, value: Any) -> str:
            """Update a user profile field.

            Use this to store structured user information (name, timezone,
            language, style, projects, preferences, or any custom field).

            Args:
                field: Profile field name (name, timezone, language, style,
                       projects, preferences, or any custom key)
                value: The value to set

            Returns:
                Confirmation message
            """
            try:
                self.vault.update_profile(field, value)
                return f"Profile field '{field}' updated successfully"
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
                return f"Error updating profile: {str(e)}"

        @self.mcp.tool()
        async def get_profile() -> dict[str, Any]:
            """Get the current user profile.

            Returns:
                Dictionary with all profile fields
            """
            try:
                return self.vault.get_profile()
            except Exception as e:
                logger.error(f"Error getting profile: {e}")
                return {"error": str(e)}

        # =====================================================================
        # Session Tools
        # =====================================================================

        @self.mcp.tool()
        async def end_session() -> str:
            """End the current session.

            Summarizes the current chat history, stores it as a session
            summary memory, and clears the chat history.

            Returns:
                The session summary or a message if nothing to summarize
            """
            try:
                summary = self.vault.end_session()
                if summary:
                    return f"Session ended. Summary stored:\n{summary}"
                return "No chat history to summarize"
            except Exception as e:
                logger.error(f"Error ending session: {e}")
                return f"Error ending session: {str(e)}"

        @self.mcp.tool()
        async def start_session(first_message: str | None = None) -> dict[str, Any]:
            """Start a new session with context loading.

            Loads the user profile, recent session summaries, and optionally
            relevant memories based on the first message.

            Args:
                first_message: Optional first message to find relevant context

            Returns:
                Dictionary with profile, recap, and relevant facts
            """
            try:
                context = self.vault.get_session_context(
                    query=first_message, top_k=5
                )
                return {
                    "profile": context["profile"],
                    "recap": context["recap"],
                    "relevant_facts": context["relevant_facts"],
                    "formatted": self.vault.get_formatted_session_context(
                        query=first_message, top_k=5
                    ),
                }
            except Exception as e:
                logger.error(f"Error starting session: {e}")
                return {"error": str(e)}

        # =====================================================================
        # Consolidation Tools
        # =====================================================================

        @self.mcp.tool()
        async def consolidate_memories(threshold: float = 0.85) -> dict[str, Any]:
            """Consolidate near-duplicate memories.

            Finds similar memories and merges them into single entries,
            removing redundancy while preserving all unique information.

            Args:
                threshold: Similarity threshold (0.0-1.0) for considering
                          memories as duplicates (default: 0.85)

            Returns:
                Statistics about the consolidation
            """
            try:
                stats = self.vault.consolidate_memories(
                    similarity_threshold=threshold
                )
                return {
                    "status": "completed",
                    "merged_groups": stats["merged_groups"],
                    "total_removed": stats["total_removed"],
                }
            except Exception as e:
                logger.error(f"Error consolidating memories: {e}")
                return {"error": str(e)}

    def run(self, transport: str = "stdio", **kwargs):
        """Run the MCP server.

        Args:
            transport: Transport method (stdio, http, sse)
            **kwargs: Additional arguments for HTTP/SSE transport (host, port)
        """
        if transport == "stdio":
            self.mcp.run(transport="stdio")
        elif transport == "http":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 8000)
            asyncio.run(self.mcp.run_http_async(host=host, port=port))
        elif transport == "sse":
            host = kwargs.get("host", "localhost")
            port = kwargs.get("port", 8000)
            self.mcp.run(transport="sse", host=host, port=port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")


def run_server():
    """Entry point for the MCP server CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="MemoVault MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport method (default: stdio)",
    )
    parser.add_argument("--host", default="localhost", help="Host for HTTP/SSE transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP/SSE transport")

    args = parser.parse_args()

    server = MemoVaultMCPServer()
    server.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    run_server()
