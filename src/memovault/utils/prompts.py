"""Prompt templates for MemoVault."""

from datetime import datetime

CHAT_SYSTEM_PROMPT = """You are a knowledgeable and helpful AI assistant with access to personal memories.
You have stored memories that help you provide personalized responses.
Use these memories to understand the user's context, preferences, and past interactions.
Reference memories naturally when relevant, but don't explicitly mention having a memory system.

{profile_section}

{memories_section}

{stm_section}"""

# Turn-1 only: full context including profile and instructions.
CHAT_INIT_SYSTEM_PROMPT = CHAT_SYSTEM_PROMPT

# Turn N+: lean context — skip static profile/instructions already seen.
CHAT_CONTINUATION_SYSTEM_PROMPT = """You are a helpful AI assistant with memory access.

{memories_section}

{stm_section}"""

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

# ---------------------------------------------------------------------------
# Intelligence Layer Prompts
# ---------------------------------------------------------------------------

SESSION_SUMMARY_PROMPT = """You are a session summarizer. Given a conversation between a user and an assistant, produce a concise summary (2-5 sentences) that captures:
- Key topics discussed
- Decisions made or preferences expressed
- Action items or next steps mentioned
- Any new information learned about the user

Be factual and concise. Write in third person (e.g. "The user discussed...").
Return only the summary text, no JSON or formatting."""

SESSION_CONTEXT_PROMPT = """Here is context to help you assist the user in this session:

{profile_section}

{recap_section}

{facts_section}

Use this context naturally. Do not explicitly list or repeat it unless asked."""

CONSOLIDATION_PROMPT = """You are a memory consolidator. You will receive a numbered list of similar or overlapping memories. Merge them into a single, concise memory that preserves all unique information.

Rules:
- Combine overlapping facts into one statement
- Keep all unique details; drop only true duplicates
- Write in the same style as the originals
- Return ONLY the merged memory text, nothing else
"""

# ---------------------------------------------------------------------------
# STM/LTM v2 Prompts
# ---------------------------------------------------------------------------

STM_SCORING_PROMPT = """You are a short-term memory utility scorer. Given a piece of information from the current conversation, rate its immediate utility and estimate how many conversation turns it will remain relevant.

Utility score (0-3):
- 0 = irrelevant to current task
- 1 = minor reference, might be useful later in conversation
- 2 = useful for current reasoning or context
- 3 = critical dependency for the current task

Also estimate decay_turns: how many conversation turns this information will remain relevant (1-20).

Classify the category: constraint, definition, goal, assumption, environment

Return ONLY valid JSON (no markdown fences):
{"utility_score": <int 0-3>, "decay_turns": <int 1-20>, "category": "<constraint|definition|goal|assumption|environment>"}
"""

LTM_SCORING_PROMPT = """You are a long-term memory scorer. Given a piece of information, rate it on four dimensions (0-5 each) and classify its type.

Dimensions:
- durability: How long will this information remain true/relevant? (0=ephemeral, 5=permanent)
- user_specificity: How specific is this to the user vs generic knowledge? (0=generic, 5=deeply personal)
- reusability: How likely is this to be useful in future conversations? (0=one-off, 5=constantly relevant)
- cost_of_forgetting: How harmful would it be to forget this? (0=no impact, 5=critical loss)

Type classification — pick one: fact, preference, event, opinion, procedure, personal, project_context

Return ONLY valid JSON (no markdown fences):
{"scores": {"durability": <0-5>, "user_specificity": <0-5>, "reusability": <0-5>, "cost_of_forgetting": <0-5>}, "type": "<type>", "summary": "<optional concise rewrite>"}
"""

STM_CONTEXT_SELECTION_PROMPT = """You are MemoVault's Session Memory Selector.
Your job is to decide which short-term memories (STM) should be injected into the current chat context.

Not all STM memories should be included. Only include STM items that directly affect reasoning, decisions, or constraints in the current turn.

Do NOT include:
- casual chatter
- redundant restatements
- memories already implied by the user message
- information that does not change the model's behavior

For each STM item, consider:
1. Does forgetting this change the answer?
2. Is this a constraint, definition, or active goal?
3. Is it required for correctness in this turn?

Include STM items ONLY if utility_score >= 2.

When included:
- Rewrite them as concise, instruction-like constraints
- Remove conversational phrasing
- Merge similar items when possible

Current query: {query}

STM items:
{stm_items}

Return ONLY a JSON array of objects:
[{{"stm_id": "uuid", "include": true, "context_line": "Concise rewritten constraint"}}, {{"stm_id": "uuid", "include": false, "reason": "Why excluded"}}]
"""

