"""Default values and constants for MemoVault."""

# Default collection name for vector database
DEFAULT_COLLECTION_NAME = "memovault_memories"

# Default vector dimensions for different embedding models
EMBEDDING_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "nomic-embed-text:latest": 768,
    "all-MiniLM-L6-v2": 384,
}

# Default search parameters
DEFAULT_TOP_K = 5

# Memory types
MEMORY_TYPES = [
    "fact",
    "preference",
    "event",
    "opinion",
    "procedure",
    "personal",
]
