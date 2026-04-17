"""Half-life decay computation for long-term memories."""

import math
from datetime import datetime

from memovault.utils.log import get_logger

logger = get_logger(__name__)


def compute_decay_factor(
    created_at: str,
    half_life_days: float | None,
    now: datetime | None = None,
) -> float:
    """Compute exponential decay factor based on half-life.

    Returns a value between 0.0 and 1.0.
    Infinite half-life (or None) returns 1.0 (no decay).

    Args:
        created_at: ISO timestamp of memory creation.
        half_life_days: Half-life in days. Infinite means no decay.
        now: Current time (defaults to datetime.now()).
    """
    if half_life_days is None or half_life_days == float("inf"):
        return 1.0

    if half_life_days <= 0:
        return 0.0

    now = now or datetime.now()
    try:
        created = datetime.fromisoformat(created_at)
    except (ValueError, TypeError):
        return 1.0

    age_days = (now - created).total_seconds() / 86400

    if age_days <= 0:
        return 1.0

    return math.pow(0.5, age_days / half_life_days)


def apply_decay_to_results(
    memories: list,
    min_factor: float = 0.1,
) -> list:
    """Filter and reorder search results by applying half-life decay.

    Memories with decay_factor below min_factor are excluded.
    Remaining memories are sorted by decay factor (freshest/most permanent first).

    Args:
        memories: List of MemoryItem objects.
        min_factor: Minimum decay factor to keep (0.0-1.0).

    Returns:
        Filtered and sorted list of MemoryItem objects.
    """
    decayed = []
    for mem in memories:
        half_life = getattr(mem.metadata, "half_life_days", None)
        created = mem.metadata.created_at
        factor = compute_decay_factor(created, half_life)
        if factor >= min_factor:
            decayed.append((mem, factor))

    decayed.sort(key=lambda x: x[1], reverse=True)
    return [mem for mem, _ in decayed]
