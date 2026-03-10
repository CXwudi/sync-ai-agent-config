"""Default file mappings for sync-ai-config."""

from __future__ import annotations

from pathlib import Path
from typing import List

from sync_ai_config.models import FileMapping, KeepMode


DEFAULT_RSYNC_OPTS = "-avzL --update --delete --human-readable --mkpath"

ALL_FILE_MAPPINGS: List[FileMapping] = [
  # Common for Agents
  FileMapping(
    relative_path=Path(".agents/skills/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="Shared agent skills",
  ),

  # Claude Code
  FileMapping(
    relative_path=Path(".claude.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.KEEP_BOTH,
    description="Claude config",
  ),
  FileMapping(
    relative_path=Path(".claude/settings.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Claude settings file",
  ),
  FileMapping(
    relative_path=Path(".claude/config.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Claude config.json file",
  ),
  FileMapping(
    relative_path=Path(".claude/CLAUDE.md"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Claude prompt file",
  ),
  FileMapping(
    relative_path=Path(".claude/agents/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="Claude subagents",
  ),
  FileMapping(
    relative_path=Path(".claude/skills/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="Claude skills",
  ),

  # Gemini CLI
  FileMapping(
    relative_path=Path(".gemini/settings.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Gemini settings",
  ),
  FileMapping(
    relative_path=Path(".gemini/AGENTS.md"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Gemini AGENTS prompt file",
  ),
  FileMapping(
    relative_path=Path(".gemini/GEMINI.md"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Gemini legacy prompt file",
  ),

  # Codex
  FileMapping(
    relative_path=Path(".codex/config.toml"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Codex config",
  ),
  FileMapping(
    relative_path=Path(".codex/auth.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Codex auth",
  ),
  FileMapping(
    relative_path=Path(".codex/AGENTS.md"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Codex prompt file",
  ),

  # OpenCode
  FileMapping(
    relative_path=Path(".config/opencode/opencode.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="OpenCode main config (JSON)",
  ),
  FileMapping(
    relative_path=Path(".config/opencode/opencode.jsonc"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="OpenCode main config (JSONC)",
  ),
  FileMapping(
    relative_path=Path(".config/opencode/AGENTS.md"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="OpenCode prompt file",
  ),
  FileMapping(
    relative_path=Path(".config/opencode/prompts/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="OpenCode custom prompts",
  ),
  FileMapping(
    relative_path=Path(".config/opencode/agents/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="OpenCode custom agents",
  ),
  FileMapping(
    relative_path=Path(".config/opencode/commands/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="OpenCode custom commands",
  ),
  FileMapping(
    relative_path=Path(".config/opencode/plugins/"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    is_directory=True,
    description="OpenCode plugins",
  ),
  FileMapping(
    relative_path=Path(".local/share/opencode/auth.json"),
    windows_relative_path=None,
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="OpenCode auth credentials",
  ),

  # Cline
  FileMapping(
    relative_path=Path(
      ".vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
    ),
    windows_relative_path=Path(
      "AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
    ),
    remote_relative_path=None,
    keep_mode=KeepMode.PREFER_LINUX,
    description="Cline MCP settings for VSCode",
  ),
  # The windows path is dependent on the user's Documents folder location, not necessarily "Documents"
  # FileMapping(
  #   relative_path=Path("Cline/Rules/"),
  #   windows_relative_path=Path("Documents/Cline/Rules/"),
  #   remote_relative_path=None,
  #   keep_mode=KeepMode.PREFER_LINUX,
  #   is_directory=True,
  #   description="Cline rules",
  # ),
]
