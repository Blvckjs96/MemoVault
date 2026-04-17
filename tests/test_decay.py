"""Tests for half-life decay computation."""

import math
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from memovault.core.decay import apply_decay_to_results, compute_decay_factor


class TestComputeDecayFactor:
    """Tests for compute_decay_factor."""

    def test_infinite_half_life(self):
        assert compute_decay_factor("2024-01-01T00:00:00", float("inf")) == 1.0

    def test_none_half_life(self):
        assert compute_decay_factor("2024-01-01T00:00:00", None) == 1.0

    def test_zero_half_life(self):
        assert compute_decay_factor("2024-01-01T00:00:00", 0) == 0.0

    def test_negative_half_life(self):
        assert compute_decay_factor("2024-01-01T00:00:00", -10) == 0.0

    def test_exact_half_life(self):
        now = datetime(2024, 7, 1)
        created = datetime(2024, 1, 1)
        half_life = (now - created).days  # ~182 days
        factor = compute_decay_factor(created.isoformat(), half_life, now=now)
        assert abs(factor - 0.5) < 0.01

    def test_no_age(self):
        now = datetime(2024, 1, 1, 12, 0, 0)
        factor = compute_decay_factor(now.isoformat(), 365, now=now)
        assert factor == 1.0

    def test_future_created(self):
        now = datetime(2024, 1, 1)
        future = datetime(2024, 6, 1)
        factor = compute_decay_factor(future.isoformat(), 365, now=now)
        assert factor == 1.0

    def test_invalid_timestamp(self):
        assert compute_decay_factor("not-a-date", 365) == 1.0

    def test_double_half_life(self):
        now = datetime(2024, 1, 1)
        created = now - timedelta(days=60)
        factor = compute_decay_factor(created.isoformat(), 30, now=now)
        # After 2 half-lives: 0.5^2 = 0.25
        assert abs(factor - 0.25) < 0.01


class TestApplyDecayToResults:
    """Tests for apply_decay_to_results."""

    def _make_memory(self, created_at: str, half_life: float | None = None):
        mem = MagicMock()
        mem.metadata.created_at = created_at
        mem.metadata.half_life_days = half_life
        return mem

    def test_infinite_half_life_kept(self):
        mem = self._make_memory("2020-01-01T00:00:00", float("inf"))
        result = apply_decay_to_results([mem])
        assert len(result) == 1

    def test_expired_filtered_out(self):
        # Very old with short half-life
        mem = self._make_memory("2020-01-01T00:00:00", 1)
        result = apply_decay_to_results([mem], min_factor=0.1)
        assert len(result) == 0

    def test_fresh_kept(self):
        now = datetime.now()
        mem = self._make_memory(now.isoformat(), 365)
        result = apply_decay_to_results([mem])
        assert len(result) == 1

    def test_sorted_by_decay(self):
        now = datetime.now()
        old = self._make_memory((now - timedelta(days=100)).isoformat(), 365)
        fresh = self._make_memory(now.isoformat(), 365)
        result = apply_decay_to_results([old, fresh])
        assert result[0] is fresh
        assert result[1] is old

    def test_none_half_life_treated_as_permanent(self):
        mem = self._make_memory("2020-01-01T00:00:00", None)
        result = apply_decay_to_results([mem])
        assert len(result) == 1
