"""Tests for the UserProfile system."""

import json
import tempfile
from pathlib import Path

from memovault.core.profile import ProfileManager, UserProfile


class TestUserProfile:
    """Tests for UserProfile model."""

    def test_default_profile(self):
        profile = UserProfile()
        assert profile.name is None
        assert profile.timezone is None
        assert profile.projects == []
        assert profile.preferences == {}
        assert profile.custom_fields == {}

    def test_profile_with_values(self):
        profile = UserProfile(
            name="Jason",
            timezone="America/New_York",
            language="English",
            projects=["MemoVault"],
        )
        assert profile.name == "Jason"
        assert profile.projects == ["MemoVault"]

    def test_to_context_string_empty(self):
        profile = UserProfile()
        assert profile.to_context_string() == ""

    def test_to_context_string_with_data(self):
        profile = UserProfile(name="Jason", timezone="EST")
        ctx = profile.to_context_string()
        assert "Jason" in ctx
        assert "EST" in ctx


class TestProfileManager:
    """Tests for ProfileManager persistence."""

    def test_load_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(data_dir=tmpdir)
            assert pm.profile.name is None

    def test_update_and_persist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(data_dir=tmpdir)
            pm.update_field("name", "Jason")
            assert pm.profile.name == "Jason"

            # Verify file was written
            profile_path = Path(tmpdir) / "profile.json"
            assert profile_path.exists()

            # Verify reloading works
            pm2 = ProfileManager(data_dir=tmpdir)
            assert pm2.profile.name == "Jason"

    def test_update_custom_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(data_dir=tmpdir)
            pm.update_field("favorite_color", "blue")
            assert pm.profile.custom_fields["favorite_color"] == "blue"

    def test_to_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(data_dir=tmpdir)
            pm.update_field("name", "Jason")
            d = pm.to_dict()
            assert d["name"] == "Jason"
            assert "projects" in d
