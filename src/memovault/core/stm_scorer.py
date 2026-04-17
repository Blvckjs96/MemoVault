"""Short-term memory utility scoring."""

import json
from typing import Any

from memovault.llm.base import BaseLLM
from memovault.utils.log import get_logger
from memovault.utils.prompts import STM_SCORING_PROMPT

logger = get_logger(__name__)

DEFAULT_STM_RESULT = {"utility_score": 1, "decay_turns": 5, "category": "constraint"}


class STMScorer:
    """Scores memories for short-term utility using the fast LLM."""

    def __init__(self, llm: BaseLLM):
        self._llm = llm

    def score(self, content: str) -> dict[str, Any]:
        """Score STM utility.

        Args:
            content: The memory text to evaluate.

        Returns:
            Dict with keys: utility_score (0-3), decay_turns (int), category (str).
        """
        messages = [
            {"role": "system", "content": STM_SCORING_PROMPT},
            {"role": "user", "content": content},
        ]

        try:
            raw = self._llm.generate(messages)
            result = self._parse_response(raw)
            logger.debug(
                f"STM scored: utility={result['utility_score']}, "
                f"decay={result['decay_turns']}, cat={result['category']}"
            )
            return result
        except Exception as e:
            logger.warning(f"STM scoring failed, using defaults: {e}")
            return dict(DEFAULT_STM_RESULT)

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        """Parse the LLM JSON response, with fallback."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return dict(DEFAULT_STM_RESULT)

        valid_categories = {"constraint", "definition", "goal", "assumption", "environment"}
        category = data.get("category", "constraint")
        if category not in valid_categories:
            category = "constraint"

        return {
            "utility_score": max(0, min(3, int(data.get("utility_score", 1)))),
            "decay_turns": max(1, min(20, int(data.get("decay_turns", 5)))),
            "category": category,
        }
