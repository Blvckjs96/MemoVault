# MemoVault

A personal memory system for AI assistants — runs entirely on your machine, stores everything locally, and integrates with Claude Code, Cursor, Gemini CLI, and Codex via lifecycle hooks.

> **Privacy first.** Nothing leaves your machine by default. Memories are stored as local files. The dashboard polls your own REST API. Plugin hooks call `localhost` only.

---

## Features

- **STM / LTM architecture** — short-term session memory with decay + long-term memory with 4-dimensional importance scoring
- **BM25 + vector search** — keyword (simple) or semantic (Qdrant) retrieval
- **MCP server** — first-class Claude Code integration with 15+ tools
- **Plugin hooks** — lifecycle hooks for Claude Code, Cursor, Gemini CLI, Codex CLI
- **Dashboard UI** — real-time web dashboard at `http://localhost:8080/ui`
- **Token economics** — tracks discovery vs read tokens and efficiency ratio
- **Fully local** — Ollama LLM + local embeddings + embedded Qdrant, zero cloud dependency

---

## Installation

### From source

```bash
git clone https://github.com/your-org/memovault
cd memovault
pip install -e .       # or: uv sync
cp .env.example .env
```

### From PyPI

```bash
pip install memovault
```

---

## Setup

### Option A — Fully local (Ollama)

**1. Install Ollama and pull models**

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

ollama pull llama3.1           # main LLM
ollama pull nomic-embed-text   # embeddings
```

**2. Configure `.env`**

```env
MEMOVAULT_LLM_BACKEND=ollama
MEMOVAULT_OLLAMA_MODEL=llama3.1:latest
MEMOVAULT_OLLAMA_API_BASE=http://localhost:11434

MEMOVAULT_EMBEDDER_BACKEND=ollama
MEMOVAULT_EMBEDDER_OLLAMA_MODEL=nomic-embed-text:latest

# simple = BM25 (no vector DB), vector = Qdrant (semantic search)
MEMOVAULT_MEMORY_BACKEND=simple

MEMOVAULT_DATA_DIR=./memovault_data
```

**3. Start**

```bash
memovault service start
open http://localhost:8080/ui
```

### Option B — OpenAI

```env
MEMOVAULT_LLM_BACKEND=openai
MEMOVAULT_OPENAI_API_KEY=sk-...
MEMOVAULT_OPENAI_MODEL=gpt-4o-mini

MEMOVAULT_EMBEDDER_BACKEND=openai
MEMOVAULT_EMBEDDER_OPENAI_MODEL=text-embedding-3-small

MEMOVAULT_MEMORY_BACKEND=vector
```

> Memory content is sent to OpenAI's API for scoring and embedding when using this backend.

---

## Claude Code — MCP Integration

Add to `~/.claude/claude.json`:

**Local (Ollama)**

```json
{
  "mcpServers": {
    "memovault": {
      "command": "memovault",
      "args": ["mcp"],
      "env": {
        "MEMOVAULT_LLM_BACKEND": "ollama",
        "MEMOVAULT_OLLAMA_MODEL": "llama3.1:latest"
      }
    }
  }
}
```

**OpenAI**

```json
{
  "mcpServers": {
    "memovault": {
      "command": "memovault",
      "args": ["mcp"],
      "env": {
        "MEMOVAULT_LLM_BACKEND": "openai",
        "MEMOVAULT_OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

---

## Plugin Hooks

Hooks automatically inject memory context before each prompt and save session summaries on exit. Requires the REST API to be running.

### Quick start

```bash
memovault service start                        # start REST API
memovault plugins install claude-code          # install hooks
```

### All platforms

```bash
memovault plugins list                         # show status for all platforms
memovault plugins install claude-code
memovault plugins install cursor
memovault plugins install gemini
memovault plugins install codex

memovault plugins uninstall claude-code        # remove hooks
```

### What each hook does

| Hook | Trigger | Action |
|------|---------|--------|
| `UserPromptSubmit` | Before every prompt | Fetches recent session summaries + relevant memories, prepends as context |
| `Stop` | When the tool exits | Summarizes the session and stores it to LTM |

### Platform details

**Claude Code** — writes hooks to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": ".*",
      "command": "memovault hook prompt-submit --api http://localhost:8080"
    }],
    "Stop": [{
      "command": "memovault hook session-end --api http://localhost:8080"
    }]
  }
}
```

**Cursor** — writes `memovault.hooks` config to Cursor's `settings.json`.

**Gemini CLI / Codex CLI** — adds a shell wrapper function to `~/.zshrc`. Run `source ~/.zshrc` once after install to activate.

### Auto-start the service on login

```bash
# Add to ~/.zshrc or ~/.bash_profile
memovault service start 2>/dev/null
```

---

## Service Management

```bash
memovault service start           # start REST API in background
memovault service start --port 9090
memovault service status
memovault service stop

# Foreground (useful for debugging)
memovault api --host 127.0.0.1 --port 8080
```

---

## License

MIT
