# MemoVault

A simplified personal memory system for AI assistants, designed for Claude Code integration via MCP.

## Features

- **MCP Server**: First-class integration with Claude Code
- **Flexible Backends**: Support for OpenAI and Ollama (local) LLMs
- **Vector Search**: Semantic memory retrieval using Qdrant
- **Simple JSON Storage**: Lightweight option for basic use cases
- **Easy Configuration**: Environment-based setup

## Quick Start

### Installation

```bash
pip install memovault

# For local embeddings (optional)
pip install memovault[local]
```

### Basic Usage

```python
from memovault import MemoVault

# Initialize with default settings (reads from .env)
mem = MemoVault()

# Add memories
mem.add("I prefer Python for backend development")
mem.add("My project deadline is March 15th")

# Search for relevant memories
results = mem.search("programming preferences")
for result in results:
    print(result.memory)

# Chat with memory context
response = mem.chat("What language should I use for my backend?")
print(response)

# Save memories to disk
mem.dump("./my_memories")
```

### Claude Code Integration

1. Configure MemoVault in your Claude Code settings:

```json
{
  "mcpServers": {
    "memovault": {
      "command": "memovault-mcp",
      "env": {
        "MEMOVAULT_LLM_BACKEND": "openai",
        "MEMOVAULT_OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

2. Use memory commands in Claude Code:
   - "Remember that I prefer dark mode"
   - "What do you know about my preferences?"

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# LLM Backend
MEMOVAULT_LLM_BACKEND=openai  # or "ollama"
MEMOVAULT_OPENAI_API_KEY=sk-...
MEMOVAULT_OPENAI_MODEL=gpt-4o-mini

# Embedder Backend
MEMOVAULT_EMBEDDER_BACKEND=openai  # or "ollama", "sentence_transformer"

# Memory Backend
MEMOVAULT_MEMORY_BACKEND=vector  # or "simple"

# Storage
MEMOVAULT_DATA_DIR=./memovault_data
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `add_memory` | Store new information |
| `search_memories` | Find relevant memories |
| `chat_with_memory` | Memory-enhanced chat |
| `get_memory` | Retrieve specific memory by ID |
| `delete_memory` | Remove a memory |
| `list_memories` | Show recent memories |
| `clear_memories` | Clear all memories |

## Architecture

```
MemoVault/
├── src/memovault/
│   ├── core/           # Main MemoVault class
│   ├── memory/         # Memory backends (simple, vector)
│   ├── llm/            # LLM providers (OpenAI, Ollama)
│   ├── embedder/       # Embedding providers
│   ├── vecdb/          # Vector database (Qdrant)
│   ├── config/         # Configuration management
│   └── api/            # MCP server & REST API
```

## License

MIT
