"""Tests for the MemoryScorer (4-dimensional LTM scoring)."""

import json
from unittest.mock import MagicMock

from memovault.core.scorer import MemoryScorer


class TestMemoryScorer:
    """Tests for LTM importance scoring and auto-classification."""

    def _make_scorer(self, llm_response: str, threshold: float = 3.5) -> MemoryScorer:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = llm_response
        return MemoryScorer(llm=mock_llm, threshold=threshold)

    def test_score_basic(self):
        response = json.dumps({
            "scores": {
                "durability": 4.0,
                "user_specificity": 3.5,
                "reusability": 3.0,
                "cost_of_forgetting": 4.5,
            },
            "type": "fact",
            "summary": "Important fact",
        })
        scorer = self._make_scorer(response)
        result = scorer.score("User's birthday is March 15")
        assert "scores" in result
        assert "final_score" in result
        assert result["type"] == "fact"
        # final = 4.0*0.3 + 3.5*0.3 + 3.0*0.2 + 4.5*0.2 = 3.75
        assert result["final_score"] == 3.75

    def test_score_half_life_personal(self):
        response = json.dumps({
            "scores": {"durability": 3, "user_specificity": 3, "reusability": 3, "cost_of_forgetting": 3},
            "type": "personal",
            "summary": "test",
        })
        scorer = self._make_scorer(response)
        result = scorer.score("test")
        assert result["half_life_days"] == float("inf")

    def test_score_half_life_project_context(self):
        response = json.dumps({
            "scores": {"durability": 2, "user_specificity": 4, "reusability": 2, "cost_of_forgetting": 3},
            "type": "project_context",
            "summary": "test",
        })
        scorer = self._make_scorer(response)
        result = scorer.score("test")
        assert result["half_life_days"] == 30

    def test_clamps_dimensions(self):
        response = json.dumps({
            "scores": {"durability": 10.0, "user_specificity": -2.0, "reusability": 3.0, "cost_of_forgetting": 3.0},
            "type": "fact",
            "summary": "test",
        })
        scorer = self._make_scorer(response)
        result = scorer.score("test")
        assert result["scores"]["durability"] == 5.0
        assert result["scores"]["user_specificity"] == 0.0

    def test_should_store_above_threshold(self):
        scorer = self._make_scorer("{}", threshold=3.5)
        scorer._max_capacity = 10000
        result = {"final_score": 4.0}
        assert scorer.should_store(result, "fact", 0)

    def test_should_store_below_threshold(self):
        scorer = self._make_scorer("{}", threshold=3.5)
        result = {"final_score": 2.0}
        assert not scorer.should_store(result, "fact", 0)

    def test_should_store_type_bias(self):
        scorer = self._make_scorer("{}", threshold=3.5)
        scorer._max_capacity = 10000
        # personal bias = -0.5, effective = 3.0
        result = {"final_score": 3.2}
        assert scorer.should_store(result, "personal", 0)
        # fact bias = +0.3, effective = 3.8
        assert not scorer.should_store(result, "fact", 0)

    def test_dynamic_threshold_empty(self):
        scorer = self._make_scorer("{}", threshold=3.5)
        assert scorer.compute_dynamic_threshold(0) == 3.5

    def test_dynamic_threshold_full(self):
        scorer = self._make_scorer("{}", threshold=3.5)
        scorer._max_capacity = 10000
        assert scorer.compute_dynamic_threshold(10000) == 4.0

    def test_parse_markdown_fences(self):
        response = '```json\n{"scores": {"durability": 3, "user_specificity": 3, "reusability": 3, "cost_of_forgetting": 3}, "type": "fact", "summary": "test"}\n```'
        scorer = self._make_scorer(response)
        result = scorer.score("test")
        assert result["final_score"] == 3.0

    def test_invalid_json_fallback(self):
        scorer = self._make_scorer("This is not JSON at all")
        result = scorer.score("Test")
        assert result["final_score"] == 2.5
        assert result["type"] is None

    def test_llm_error_fallback(self):
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM error")
        scorer = MemoryScorer(llm=mock_llm, threshold=3.5)
        result = scorer.score("Test")
        assert result["final_score"] == 2.5
