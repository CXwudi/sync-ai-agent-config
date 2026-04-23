"""Tests for packaged default sync mappings."""

from __future__ import annotations

import tomllib
from pathlib import Path, PureWindowsPath

from sync_ai_config.mappings import (
  ALL_FILE_MAPPINGS,
  load_default_file_mappings,
  read_default_mappings_text,
)
from sync_ai_config.models import FileMapping, FileMappingConfig, KeepMode


def load_packaged_default_mappings() -> list[FileMapping]:
  """Load packaged default mappings through the public resource reader."""
  data = tomllib.loads(read_default_mappings_text())
  return FileMappingConfig.model_validate(data).mappings


def test_packaged_default_toml_parses_successfully() -> None:
  """The packaged default TOML should parse into file mappings."""
  mappings = load_packaged_default_mappings()
  loaded_mappings = load_default_file_mappings()

  assert [mapping.model_dump() for mapping in mappings] == [
    mapping.model_dump() for mapping in loaded_mappings
  ]
  assert len(mappings) == 26


def test_default_mapping_key_compatibility_signals() -> None:
  """Default mappings should preserve the previous active mapping data."""
  mappings = load_packaged_default_mappings()

  first_mapping = mappings[0]
  claude_json = mappings[1]
  claude_agents = mappings[5]
  claude_skills = mappings[6]
  codex_plugins = mappings[13]
  pi_settings = mappings[14]
  opencode_main = mappings[17]
  opencode_directories = mappings[20:24]
  final_mapping = mappings[-1]

  assert first_mapping.relative_path == Path(".agents/skills")
  assert first_mapping.keep_mode == KeepMode.PREFER_LINUX
  assert first_mapping.is_directory is True

  assert claude_json.relative_path == Path(".claude.json")
  assert claude_json.keep_mode == KeepMode.KEEP_BOTH

  assert claude_agents.relative_path == Path(".claude/agents")
  assert claude_agents.is_directory is True
  assert claude_skills.relative_path == Path(".claude/skills")
  assert claude_skills.is_directory is True

  assert codex_plugins.relative_path == Path(".codex/plugins")
  assert codex_plugins.is_directory is True

  assert pi_settings.relative_path == Path(".pi/agent/settings.json")
  assert opencode_main.relative_path == Path(".config/opencode/opencode.json")

  assert [mapping.relative_path for mapping in opencode_directories] == [
    Path(".config/opencode/prompts"),
    Path(".config/opencode/agents"),
    Path(".config/opencode/commands"),
    Path(".config/opencode/plugins"),
  ]
  assert all(mapping.is_directory for mapping in opencode_directories)

  assert final_mapping.relative_path == Path(
    ".vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
  )
  assert final_mapping.windows_relative_path == Path(
    "AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
  )
  assert final_mapping.remote_relative_path is None


def test_default_toml_excludes_inactive_cline_rules_mapping() -> None:
  """The default TOML should not include mappings that were commented out."""
  assert "Cline/Rules" not in read_default_mappings_text()


def test_default_mappings_have_no_absolute_paths() -> None:
  """Default path fragments should stay relative to their configured bases."""
  for mapping in load_packaged_default_mappings():
    path_values = [
      mapping.relative_path,
      mapping.windows_relative_path,
      mapping.remote_relative_path,
    ]
    for path_value in path_values:
      if path_value is None:
        continue
      assert not path_value.is_absolute()
      assert not PureWindowsPath(path_value.as_posix()).is_absolute()
      assert not PureWindowsPath(path_value.as_posix()).drive


def test_legacy_all_file_mappings_loads_from_packaged_default() -> None:
  """The compatibility export should reflect the packaged default TOML."""
  expected_mappings = load_packaged_default_mappings()

  assert [mapping.model_dump() for mapping in ALL_FILE_MAPPINGS] == [
    mapping.model_dump() for mapping in expected_mappings
  ]
