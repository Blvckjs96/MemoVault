"""Base configuration class for MemoVault."""

import json
import os
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseConfig(BaseModel):
    """Base configuration class.

    All configurations should inherit from this class.
    Uses Pydantic's ConfigDict to enforce strict validation.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    @classmethod
    def from_json_file(cls, json_path: str) -> "BaseConfig":
        """Load configuration from a JSON file."""
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def to_json_file(self, json_path: str) -> None:
        """Dump configuration to a JSON file."""
        dir_path = os.path.dirname(json_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key, default)
