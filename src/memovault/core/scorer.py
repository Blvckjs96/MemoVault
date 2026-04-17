"""Importance scoring and auto-classification for memories."""

import json
from typing import Any

from memovault.llm.base import BaseLLM
from memovault.utils.log import get_logger
from memovault.utils.prompts import LTM_SCORING_PROMPT

logger = get_logger(__name__)


class MemoryScorer:
    """Scores memory importance using 4-dimensional LTM scoring.

    Dimensions (0-5 each):
    - durability: How long will this remain true/relevant?
    - user_specificity: How specific is this to the user?
    - reusability: How likely to be useful in future conversations?
    - cost_of_forgetting: How harmful would it be to forget this?

    Final score = weighted sum, compared against dynamic threshold
    with type bias and memory pressure adjustments.
    """

    DIMENSION_WEIGHTS = {
        "durability": 0.3,
        "user_specificity": 0.3,
        "reusability": 0.2,
        "cost_of_forgetting": 0.2,
    }

    TYPE_BIAS = {
        "personal": -0.5,
        "preference": -0.3,
        "procedure": 0.0,
        "fact": 0.3,
        "project_context": 0.2,
        "event": 0.0,
        "opinion": 0.0,
    }

    HALF_LIFE_DAYS: dict[str, float] = {
        "personal": float("inf"),
        "preference": float("inf"),
        "procedure": 180,
        "fact": 365,
        "project_context": 30,
        "event": 90,
        "opinion": 180,
    }

    def __init__(
        self,
        llm: BaseLLM,
        threshold: float = 3.5,
    ):
        """Initialize the scorer.

        Args:
            llm: LLM instance to use for scoring.
            threshold: Base LTM threshold for admission.
        """
        self._llm = llm
        self.threshold = threshold

    def score(self, content: str) -> dict[str, Any]:
        """Score a memory using 4-dimensional LTM scoring.

        Args:
            content: The memory text to evaluate.

        Returns:
            Dict with keys: scores (dict), final_score (float), type (str),
            half_life_days (float), summary (str).
        """
        messages = [
            {"role": "system", "content": LTM_SCORING_PROMPT},
            {"role": "user", "content": content},
        ]

        try:
            raw = self._llm.generate(messages)
            result = self._parse_response(raw)

            # Compute weighted final score
            scores = result["scores"]
            final = sum(
                scores.get(k, 0) * w for k, w in self.DIMENSION_WEIGHTS.items()
            )
            result["final_score"] = round(final, 2)

            # Assign half-life based on type
            mem_type = result.get("type", "fact")
            result["half_life_days"] = self.HALF_LIFE_DAYS.get(mem_type, 365)

            logger.debug(
                f"LTM scored: final={result['final_score']}, type={mem_type}, "
                f"half_life={result['half_life_days']}"
            )
            return result
        except Exception as e:
            logger.warning(f"LTM scoring failed, using defaults: {e}")
            return {
                "scores": {k: 2.5 for k in self.DIMENSION_WEIGHTS},
                "final_score": 2.5,
                "type": None,
                "half_life_days": 365,
                "summary": content,
            }

    def should_store(
        self, score_result: dict[str, Any], memory_type: str, memory_count: int
    ) -> bool:
        """Check whether a scored memory meets the dynamic LTM threshold.

        threshold = base + pressure + type_bias
        """
        dynamic = self.compute_dynamic_threshold(memory_count)
        bias = self.TYPE_BIAS.get(memory_type or "fact", 0.0)
        effective_threshold = dynamic + bias
        return score_result.get("final_score", 0) >= effective_threshold

    def compute_dynamic_threshold(self, memory_count: int) -> float:
        """Compute dynamic threshold based on memory pressure.

        threshold = base_threshold + memory_pressure * 0.5
        """
        max_cap = max(1, getattr(self, "_max_capacity", 10000))
        pressure = min(memory_count / max_cap, 1.0)
        return self.threshold + pressure * 0.5

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        """Parse the LTM JSON response."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {
                "scores": {"durability": 2.5, "user_specificity": 2.5,
                           "reusability": 2.5, "cost_of_forgetting": 2.5},
                "type": None,
                "summary": raw.strip(),
            }

        scores_raw = data.get("scores", {})
        scores = {}
        for dim in ("durability", "user_specificity", "reusability", "cost_of_forgetting"):
            val = scores_raw.get(dim, 2.5)
            scores[dim] = max(0.0, min(5.0, float(val)))

        return {
            "scores": scores,
            "type": data.get("type"),
            "summary": data.get("summary", ""),
        }
