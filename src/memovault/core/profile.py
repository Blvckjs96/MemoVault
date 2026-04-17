"""User profile system for MemoVault."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from memovault.utils.log import get_logger

logger = get_logger(__name__)

PROFILE_FILENAME = "profile.json"


class UserProfile(BaseModel):
    """Structured user profile stored as JSON (separate from vector DB)."""

    name: str | None = Field(default=None, description="User's name")
    timezone: str | None = Field(default=None, description="User's timezone")
    language: str | None = Field(default=None, description="Preferred language")
    style: str | None = Field(
        default=None, description="Communication style preference"
    )
    projects: list[str] = Field(
        default_factory=list, description="Active projects"
    )
    preferences: dict[str, Any] = Field(
        default_factory=dict, description="General preferences"
    )
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Any additional user-defined fields"
    )

    def to_context_string(self) -> str:
        """Format profile as a string suitable for LLM system prompt injection."""
        parts = []
        if self.name:
            parts.append(f"Name: {self.name}")
        if self.timezone:
            parts.append(f"Timezone: {self.timezone}")
        if self.language:
            parts.append(f"Language: {self.language}")
        if self.style:
            parts.append(f"Communication style: {self.style}")
        if self.projects:
            parts.append(f"Active projects: {', '.join(self.projects)}")
        if self.preferences:
            prefs = "; ".join(f"{k}: {v}" for k, v in self.preferences.items())
            parts.append(f"Preferences: {prefs}")
        if self.custom_fields:
            for k, v in self.custom_fields.items():
                parts.append(f"{k}: {v}")
        return "\n".join(parts) if parts else ""


class ProfileManager:
    """Manages user profile persistence via JSON file."""

    def __init__(self, data_dir: str | Path):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._data_dir / PROFILE_FILENAME
        self._profile = self._load()

    @property
    def profile(self) -> UserProfile:
        return self._profile

    def _load(self) -> UserProfile:
        """Load profile from disk, or return empty profile."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                logger.info(f"Profile loaded from {self._path}")
                return UserProfile(**data)
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}")
        return UserProfile()

    def save(self) -> None:
        """Persist profile to disk."""
        self._path.write_text(
            self._profile.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.debug(f"Profile saved to {self._path}")

    def update_field(self, field: str, value: Any) -> None:
        """Update a single profile field and save.

        Args:
            field: Field name (must be a valid UserProfile field or goes into custom_fields).
            value: New value for the field.
        """
        if field in UserProfile.model_fields:
            setattr(self._profile, field, value)
        else:
            self._profile.custom_fields[field] = value
        self.save()
        logger.info(f"Profile field '{field}' updated")

    def to_dict(self) -> dict[str, Any]:
        """Return profile as a dictionary."""
        return self._profile.model_dump()

    def to_context_string(self) -> str:
        """Format profile for LLM context injection."""
        return self._profile.to_context_string()
