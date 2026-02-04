"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Use simple memory backend for tests by default
    os.environ.setdefault("MEMOVAULT_MEMORY_BACKEND", "simple")
    os.environ.setdefault("MEMOVAULT_LOG_LEVEL", "WARNING")
    yield
