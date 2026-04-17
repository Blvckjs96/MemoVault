"""Tests for STMScorer."""

from unittest.mock import MagicMock

from memovault.core.stm_scorer import STMScorer


class TestSTMScorer:
    """Tests for short-term memory utility scoring."""

    def _make_scorer(self, llm_response: str) -> STMScorer:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = llm_response
        return STMScorer(llm=mock_llm)

    def test_score_high_utility(self):
        scorer = self._make_scorer(
            '{"utility_score": 3, "decay_turns": 10, "category": "goal"}'
        )
        result = scorer.score("Build the authentication module")
        assert result["utility_score"] == 3
        assert result["decay_turns"] == 10
        assert result["category"] == "goal"

    def test_score_low_utility(self):
        scorer = self._make_scorer(
            '{"utility_score": 0, "decay_turns": 2, "category": "assumption"}'
        )
        result = scorer.score("ok sure")
        assert result["utility_score"] == 0
        assert result["decay_turns"] == 2

    def test_clamp_utility_score(self):
        scorer = self._make_scorer(
            '{"utility_score": 10, "decay_turns": 5, "category": "constraint"}'
        )
        result = scorer.score("test")
        assert result["utility_score"] == 3  # clamped to max

    def test_clamp_decay_turns(self):
        scorer = self._make_scorer(
            '{"utility_score": 2, "decay_turns": 100, "category": "constraint"}'
        )
        result = scorer.score("test")
        assert result["decay_turns"] == 20  # clamped to max

    def test_invalid_category_fallback(self):
        scorer = self._make_scorer(
            '{"utility_score": 2, "decay_turns": 5, "category": "invalid_type"}'
        )
        result = scorer.score("test")
        assert result["category"] == "constraint"  # fallback

    def test_valid_categories(self):
        for cat in ("constraint", "definition", "goal", "assumption", "environment"):
            scorer = self._make_scorer(
                f'{{"utility_score": 2, "decay_turns": 5, "category": "{cat}"}}'
            )
            result = scorer.score("test")
            assert result["category"] == cat

    def test_markdown_fences(self):
        scorer = self._make_scorer(
            '```json\n{"utility_score": 2, "decay_turns": 5, "category": "goal"}\n```'
        )
        result = scorer.score("test")
        assert result["utility_score"] == 2

    def test_invalid_json_fallback(self):
        scorer = self._make_scorer("This is not JSON")
        result = scorer.score("test")
        assert result["utility_score"] == 1
        assert result["decay_turns"] == 5
        assert result["category"] == "constraint"

    def test_llm_error_fallback(self):
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM error")
        scorer = STMScorer(llm=mock_llm)
        result = scorer.score("test")
        assert result["utility_score"] == 1
        assert result["decay_turns"] == 5
