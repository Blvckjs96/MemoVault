# Claude Code Setup Guide for MemoVault

This guide explains how to configure MemoVault as an MCP server for Claude Code.

## Prerequisites

1. Install MemoVault:
   ```bash
   pip install memovault
   ```

2. Set up your environment:
   ```bash
   # Create .env file or export variables
   export MEMOVAULT_LLM_BACKEND=openai
   export MEMOVAULT_OPENAI_API_KEY=sk-your-key-here
   export MEMOVAULT_OPENAI_MODEL=gpt-4o-mini
   ```

## Configuration

### Option 1: Global Claude Code Settings

Add to your Claude Code settings file (`~/.config/claude-code/settings.json` or equivalent):

```json
{
  "mcpServers": {
    "memovault": {
      "command": "memovault-mcp",
      "env": {
        "MEMOVAULT_LLM_BACKEND": "openai",
        "MEMOVAULT_OPENAI_API_KEY": "sk-your-key-here",
        "MEMOVAULT_OPENAI_MODEL": "gpt-4o-mini",
        "MEMOVAULT_EMBEDDER_BACKEND": "openai",
        "MEMOVAULT_EMBEDDER_OPENAI_MODEL": "text-embedding-3-small"
      }
    }
  }
}
```

### Option 2: Project-specific Configuration

Add to your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "memovault": {
      "command": "python",
      "args": ["-m", "memovault.api.mcp"],
      "env": {
        "MEMOVAULT_DATA_DIR": "./project_memories",
        "MEMOVAULT_LLM_BACKEND": "openai",
        "MEMOVAULT_OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### Option 3: Using Local Ollama

For fully local operation:

```json
{
  "mcpServers": {
    "memovault": {
      "command": "memovault-mcp",
      "env": {
        "MEMOVAULT_LLM_BACKEND": "ollama",
        "MEMOVAULT_OLLAMA_MODEL": "llama3.1:latest",
        "MEMOVAULT_EMBEDDER_BACKEND": "ollama",
        "MEMOVAULT_EMBEDDER_OLLAMA_MODEL": "nomic-embed-text:latest"
      }
    }
  }
}
```

## Usage in Claude Code

Once configured, you can use natural language to interact with your memories:

### Storing Memories

- "Remember that I prefer Python for backend development"
- "Store this: My project deadline is March 15th"
- "Add to memory: I like dark mode in all applications"

### Recalling Memories

- "What do you remember about my preferences?"
- "Search for anything about my projects"
- "What's my favorite programming language?"

### Memory-Enhanced Chat

- "Given what you know about me, what language should I use for this backend?"
- "Based on my preferences, suggest some VS Code themes"

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `add_memory` | Store new information |
| `search_memories` | Find relevant memories |
| `chat_with_memory` | Memory-enhanced chat |
| `get_memory` | Retrieve specific memory by ID |
| `delete_memory` | Remove a memory |
| `list_memories` | Show recent memories |
| `clear_memories` | Clear all memories |
| `memory_status` | Check system status |

## Data Persistence

By default, memories are stored in `./memovault_data`. Configure with:

```bash
export MEMOVAULT_DATA_DIR=/path/to/your/data
```

## Troubleshooting

### MCP Server Not Starting

1. Check that MemoVault is installed: `pip show memovault`
2. Test the server manually: `memovault-mcp`
3. Check environment variables are set correctly

### Memory Search Not Working

1. Ensure embedder backend is configured
2. For OpenAI: verify API key is valid
3. For Ollama: ensure the embedding model is pulled

### Slow Performance

1. Consider using a smaller embedding model
2. For Ollama: ensure GPU acceleration is enabled
3. Limit `top_k` for searches

## Example Session

```
User: Remember that I prefer TypeScript for frontend projects