"""Platform-specific hook installers for MemoVault."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from memovault.utils.log import get_logger


def _validate_api_url(url: str) -> str:
    """Validate that a URL is safe to embed in shell scripts.

    Raises ValueError for non-http/https schemes or shell metacharacters.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"api_url must use http or https, got: {url!r}")
    # Reject shell metacharacters that could break out of the quoted string
    if re.search(r'[`$"\\;\n\r|&<>!{}()\[\]]', url):
        raise ValueError(
            f"api_url contains characters that are unsafe in shell scripts: {url!r}"
        )
    if len(url) > 256:
        raise ValueError("api_url is too long (max 256 chars)")
    return url

logger = get_logger(__name__)

_REGISTRY: dict[str, type[Platform]] = {}


def _register(cls: type[Platform]) -> type[Platform]:
    _REGISTRY[cls.name] = cls
    return cls


def list_platforms() -> list[str]:
    return sorted(_REGISTRY.keys())


class Platform(ABC):
    name: str
    description: str

    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = _validate_api_url(api_url)

    @abstractmethod
    def detect(self) -> bool:
        """Return True if the platform is installed on this machine."""

    @abstractmethod
    def install(self) -> None:
        """Write lifecycle hooks for this platform."""

    @abstractmethod
    def uninstall(self) -> None:
        """Remove MemoVault lifecycle hooks for this platform."""

    @abstractmethod
    def status(self) -> dict[str, Any]:
        """Return current installation state."""


# ── Claude Code ───────────────────────────────────────────────────────────────

@_register
class ClaudeCodePlatform(Platform):
    name = "claude-code"
    description = "Claude Code CLI — hooks into UserPromptSubmit and Stop lifecycle"

    _settings_path = Path.home() / ".claude" / "settings.json"

    def detect(self) -> bool:
        return shutil.which("claude") is not None or self._settings_path.exists()

    def install(self) -> None:
        path = self._settings_path
        path.parent.mkdir(parents=True, exist_ok=True)

        settings: dict[str, Any] = {}
        if path.exists():
            try:
                settings = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("Could not parse existing Claude Code settings.json — starting fresh")

        hooks = settings.setdefault("hooks", {})

        # UserPromptSubmit — prepend memory context
        prompt_hooks = hooks.setdefault("UserPromptSubmit", [])
        if not any(h.get("description", "").startswith("MemoVault") for h in prompt_hooks):
            prompt_hooks.append({
                "matcher": ".*",
                "command": f"memovault hook prompt-submit --api {self.api_url}",
                "description": "MemoVault: inject relevant memory context",
            })

        # Stop — save session summary
        stop_hooks = hooks.setdefault("Stop", [])
        if not any(h.get("description", "").startswith("MemoVault") for h in stop_hooks):
            stop_hooks.append({
                "command": f"memovault hook session-end --api {self.api_url}",
                "description": "MemoVault: save session summary",
            })

        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓  Hooks written to {path}")

    def uninstall(self) -> None:
        path = self._settings_path
        if not path.exists():
            print("  ℹ  No Claude Code settings.json found — nothing to remove")
            return

        settings = json.loads(path.read_text(encoding="utf-8"))
        hooks = settings.get("hooks", {})

        for key in ("UserPromptSubmit", "Stop"):
            hooks[key] = [
                h for h in hooks.get(key, [])
                if not h.get("description", "").startswith("MemoVault")
            ]

        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓  MemoVault hooks removed from {path}")

    def status(self) -> dict[str, Any]:
        if not self._settings_path.exists():
            return {"installed": False, "path": str(self._settings_path)}
        settings = json.loads(self._settings_path.read_text(encoding="utf-8"))
        hooks = settings.get("hooks", {})
        prompt_hooked = any(
            h.get("description", "").startswith("MemoVault")
            for h in hooks.get("UserPromptSubmit", [])
        )
        stop_hooked = any(
            h.get("description", "").startswith("MemoVault")
            for h in hooks.get("Stop", [])
        )
        return {
            "installed": prompt_hooked and stop_hooked,
            "prompt_hook": prompt_hooked,
            "stop_hook": stop_hooked,
            "path": str(self._settings_path),
        }


# ── Cursor ────────────────────────────────────────────────────────────────────

@_register
class CursorPlatform(Platform):
    name = "cursor"
    description = "Cursor IDE — injects memory context via background hooks"

    _settings_candidates = [
        Path.home() / ".cursor" / "settings.json",
        Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "settings.json",
        Path.home() / ".config" / "Cursor" / "User" / "settings.json",
    ]

    def _find_settings(self) -> Path | None:
        for p in self._settings_candidates:
            if p.exists():
                return p
        return None

    def detect(self) -> bool:
        return shutil.which("cursor") is not None or self._find_settings() is not None

    def install(self) -> None:
        path = self._find_settings() or self._settings_candidates[0]
        path.parent.mkdir(parents=True, exist_ok=True)

        settings: dict[str, Any] = {}
        if path.exists():
            try:
                settings = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        hooks = settings.setdefault("memovault.hooks", {})
        hooks["enabled"] = True
        hooks["api_url"] = self.api_url
        hooks["inject_on_prompt"] = True
        hooks["save_session_on_exit"] = True

        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓  MemoVault config written to {path}")
        print("  ℹ  Cursor hooks use the background REST API — make sure `memovault api` is running")

    def uninstall(self) -> None:
        path = self._find_settings()
        if not path:
            print("  ℹ  No Cursor settings found — nothing to remove")
            return
        settings = json.loads(path.read_text(encoding="utf-8"))
        settings.pop("memovault.hooks", None)
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓  MemoVault config removed from {path}")

    def status(self) -> dict[str, Any]:
        path = self._find_settings()
        if not path:
            return {"installed": False}
        settings = json.loads(path.read_text(encoding="utf-8"))
        cfg = settings.get("memovault.hooks", {})
        return {"installed": cfg.get("enabled", False), "path": str(path), "config": cfg}


# ── Gemini CLI ────────────────────────────────────────────────────────────────

@_register
class GeminiPlatform(Platform):
    name = "gemini"
    description = "Gemini CLI — wraps `gemini` command to inject memory context"

    _shell_init_files = [
        Path.home() / ".zshrc",
        Path.home() / ".bashrc",
        Path.home() / ".bash_profile",
    ]

    _MARKER_START = "# <<< MemoVault gemini hook >>>"
    _MARKER_END   = "# <<< /MemoVault gemini hook >>>"

    def _active_shell_rc(self) -> Path:
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            return Path.home() / ".zshrc"
        return Path.home() / ".bashrc"

    def detect(self) -> bool:
        return shutil.which("gemini") is not None

    def _hook_block(self) -> str:
        # api_url is pre-validated (no shell metacharacters, http/https only)
        return f"""{self._MARKER_START}
_MEMOVAULT_API='{self.api_url}'
gemini() {{
  local query="$*"
  local context
  context=$(curl -sf "${{_MEMOVAULT_API}}/memories/search" \\
    -H 'Content-Type: application/json' \\
    -d "{{\"query\": \"$query\", \"top_k\": 5}}" 2>/dev/null | \\
    python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    mems=[m['memory'] for m in d.get('memories',[])]
    if mems:
        print('[Memory context]')
        for m in mems: print('-',m)
        print()
except: pass
" 2>/dev/null)
  if [ -n "$context" ]; then
    command gemini "$@" <<EOF
$context
$query
EOF
  else
    command gemini "$@"
  fi
}}
{self._MARKER_END}"""

    def install(self) -> None:
        rc = self._active_shell_rc()
        rc.touch()
        content = rc.read_text(encoding="utf-8")
        if self._MARKER_START in content:
            print(f"  ℹ  MemoVault gemini hook already present in {rc}")
            return
        with rc.open("a", encoding="utf-8") as f:
            f.write("\n" + self._hook_block() + "\n")
        print(f"  ✓  Gemini wrapper written to {rc}")
        print(f"  ℹ  Run `source {rc}` or open a new terminal to activate")

    def uninstall(self) -> None:
        for rc in self._shell_init_files:
            if not rc.exists():
                continue
            content = rc.read_text(encoding="utf-8")
            if self._MARKER_START not in content:
                continue
            start = content.find(self._MARKER_START)
            end = content.find(self._MARKER_END) + len(self._MARKER_END)
            rc.write_text(content[:start].rstrip() + "\n" + content[end:].lstrip(), encoding="utf-8")
            print(f"  ✓  MemoVault gemini hook removed from {rc}")
            return
        print("  ℹ  No MemoVault gemini hook found — nothing to remove")

    def status(self) -> dict[str, Any]:
        for rc in self._shell_init_files:
            if rc.exists() and self._MARKER_START in rc.read_text(encoding="utf-8"):
                return {"installed": True, "path": str(rc)}
        return {"installed": False}


# ── Codex CLI ─────────────────────────────────────────────────────────────────

@_register
class CodexPlatform(Platform):
    name = "codex"
    description = "OpenAI Codex CLI — wraps `codex` command to inject memory context"

    _MARKER_START = "# <<< MemoVault codex hook >>>"
    _MARKER_END   = "# <<< /MemoVault codex hook >>>"

    def _active_shell_rc(self) -> Path:
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            return Path.home() / ".zshrc"
        return Path.home() / ".bashrc"

    def detect(self) -> bool:
        return shutil.which("codex") is not None

    def _hook_block(self) -> str:
        # api_url is pre-validated (no shell metacharacters, http/https only)
        return f"""{self._MARKER_START}
_MEMOVAULT_API='{self.api_url}'
codex() {{
  local query="$*"
  local context
  context=$(curl -sf "${{_MEMOVAULT_API}}/memories/search" \\
    -H 'Content-Type: application/json' \\
    -d "{{\"query\": \"$query\", \"top_k\": 5}}" 2>/dev/null | \\
    python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    mems=[m['memory'] for m in d.get('memories',[])]
    if mems:
        print('[Relevant memories]')
        for m in mems: print('-',m)
        print()
except: pass
" 2>/dev/null)
  if [ -n "$context" ]; then
    command codex --system-prompt "$context" "$@"
  else
    command codex "$@"
  fi
}}
{self._MARKER_END}"""

    def install(self) -> None:
        rc = self._active_shell_rc()
        rc.touch()
        content = rc.read_text(encoding="utf-8")
        if self._MARKER_START in content:
            print(f"  ℹ  MemoVault codex hook already present in {rc}")
            return
        with rc.open("a", encoding="utf-8") as f:
            f.write("\n" + self._hook_block() + "\n")
        print(f"  ✓  Codex wrapper written to {rc}")
        print(f"  ℹ  Run `source {rc}` or open a new terminal to activate")

    def uninstall(self) -> None:
        for rc in [Path.home() / ".zshrc", Path.home() / ".bashrc", Path.home() / ".bash_profile"]:
            if not rc.exists():
                continue
            content = rc.read_text(encoding="utf-8")
            if self._MARKER_START not in content:
                continue
            start = content.find(self._MARKER_START)
            end = content.find(self._MARKER_END) + len(self._MARKER_END)
            rc.write_text(content[:start].rstrip() + "\n" + content[end:].lstrip(), encoding="utf-8")
            print(f"  ✓  MemoVault codex hook removed from {rc}")
            return
        print("  ℹ  No MemoVault codex hook found — nothing to remove")

    def status(self) -> dict[str, Any]:
        for rc in [Path.home() / ".zshrc", Path.home() / ".bashrc"]:
            if rc.exists() and self._MARKER_START in rc.read_text(encoding="utf-8"):
                return {"installed": True, "path": str(rc)}
        return {"installed": False}


# ── Installer facade ──────────────────────────────────────────────────────────

class PluginInstaller:
    """Facade for installing / uninstalling MemoVault hooks across platforms."""

    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = _validate_api_url(api_url)

    def _get(self, name: str) -> Platform:
        if name not in _REGISTRY:
            raise ValueError(f"Unknown platform '{name}'. Available: {list_platforms()}")
        return _REGISTRY[name](api_url=self.api_url)

    def install(self, name: str) -> None:
        p = self._get(name)
        print(f"Installing MemoVault hooks for {name}…")
        if not p.detect():
            print(f"  ⚠  {name} does not appear to be installed, but proceeding anyway")
        p.install()

    def uninstall(self, name: str) -> None:
        p = self._get(name)
        print(f"Uninstalling MemoVault hooks for {name}…")
        p.uninstall()

    def status_all(self) -> list[dict[str, Any]]:
        rows = []
        for name, cls in _REGISTRY.items():
            p = cls(api_url=self.api_url)
            s = p.status()
            rows.append({
                "platform": name,
                "description": cls.description,
                "detected": p.detect(),
                **s,
            })
        return rows
