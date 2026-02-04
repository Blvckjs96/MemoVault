"""Prompt templates for MemoVault."""

from datetime import datetime

CHAT_SYSTEM_PROMPT = """You are a knowledgeable and helpful AI assistant with access to personal memories.
You have stored memories that help you provide personalized responses.
Use these memories to understand the user's context, preferences, and past interactions.
Reference memories naturally when relevant, but don't explicitly mention having a memory system.

{memories_section}"""

EXTRACTION_PROMPT = f"""You are a memory extractor. Your task is to extract important information from conversations that should be remembered.

Current date and time: {datetime.now().isoformat()}

Guidelines:
- Extract facts, preferences, events, opinions, and important details
- Each memory should be self-contained and understandable on its own
- Rephrase content to be clear and concise
- Focus on information that would be useful to remember for future conversations
- Ignore trivial or transient information

Return your response as a JSON array of memory objects:
[
    {{"memory": "User prefers Python for backend development", "type": "preference"}},
    {{"memory": "User has a project deadline on March 15th", "type": "event"}}
]

Types can be: "fact", "preference", "event", "opinion", "procedure", "personal"

Only return the JSON array, no other text.

Conversation to extract from:
{{messages}}

JSON Output:"""

SIMPLE_SEARCH_PROMPT = """Given the following memories and query, return the most relevant memories.

Query: {query}

Memories:
{memories}

Return the indices of the most relevant memories (0-indexed) as a JSON array.
Only return the JSON array, no other text.
"""
