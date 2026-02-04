"""MCP Server for Claude Code integration."""

import asyncio
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from memovault.core.memovault import MemoVault
from memovault.memory.item import MemoryItem
from memovault.utils.log import get_logger

load_dotenv()
logger = get_logger(__name__)


class MemoVaultMCPServer:
    """MCP Server for MemoVault - integrates with Claude Code."""

    def __init__(self, memovault: MemoVault | None = None):
        """Initialize the MCP server.

        Args:
            memovault: Optional MemoVault instance. If not provided, creates one.
        """
        self.mcp = FastMCP("MemoVault Memory System")

        if memovault is None:
            self.vault = MemoVault()
        else:
            self.vault = memovault

        self._setup_tools()
        logger.info("MemoVault MCP Server initialized")

    def _setup_tools(self):
        """Set up MCP tools."""

        @self.mcp.tool()
        async def add_memory(content: str, memory_type: str | None = None) -> str:
            """Store new information in memory.

            Use this to remember facts, preferences, events, or any important
            information the user wants to persist across sessions.

            Args:
                content: The information to remember
                memory_type: Optional type (fact, preference, event, opinion, procedure, personal)

            Returns:
                Confirmation message with the memory ID
            """
            try:
                metadata = {}
                if memory_type:
                    metadata["type"] = memory_type

                ids = self.vault.add(content, **metadata)
                return f"Memory stored successfully (ID: {ids[0]})"
            except Exception as e:
                logger.error(f"Error adding memory: {e}")
                return f"Error storing memory: {str(e)}"

        @self.mcp.tool()
        async def search_memories(query: str, top_k: int = 5) -> dict[str, Any]:
            """Search for relevant memories.

            Use this to find stored information related to a topic or question.

            Args:
                query: What to search for
                top_k: Maximum number of results (default: 5)

            Returns:
                Dictionary with matching memories
            """
            try:
                results = self.vault.search(query, top_k)
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
                return {
                    "status": "active",
                    "memory_count": self.vault.count(),
                    "backend": self.vault._memory_config.backend,
                }
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return {"status": "error", "error": str(e)}

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
