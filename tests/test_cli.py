"""Tests for CLI argument parsing and runtime config helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from sync_ai_config.cli import (
  CliArgs,
  create_argument_parser,
  mapping_config_path_from_args,
  parse_cli_args,
)
from sync_ai_config.mapping_config import SYNC_LISTING_CONFIG_ENV
from sync_ai_config.models import Operation


def test_config_option_parses_as_mapping_config_path() -> None:
  """The parser should expose --config without affecting the operation."""
  parser = create_argument_parser()

  args = parse_cli_args(parser, ["--config", "custom.toml", "push"])

  assert args.config == "custom.toml"
  assert args.operation == Operation.PUSH


def test_config_help_documents_custom_mapping_behavior() -> None:
  """The --config help text should document TOML, precedence, and replacement."""
  help_text = create_argument_parser().format_help()

  assert "--config PATH" in help_text
  assert "TOML mapping config path" in help_text
  assert SYNC_LISTING_CONFIG_ENV in help_text
  assert "replaces the packaged" in help_text
  assert "defaults" in help_text


def test_mapping_config_path_from_args_prefers_cli_over_env(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """CLI --config should take precedence over SYNC_LISTING_CONFIG."""
  cli_path = tmp_path / "cli.toml"
  env_path = tmp_path / "env.toml"
  monkeypatch.setenv(SYNC_LISTING_CONFIG_ENV, str(env_path))

  path = mapping_config_path_from_args(CliArgs(config=str(cli_path)))

  assert path == cli_path


def test_mapping_config_path_from_args_uses_env_without_cli(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """SYNC_LISTING_CONFIG should be used when --config is absent."""
  env_path = tmp_path / "env.toml"
  monkeypatch.setenv(SYNC_LISTING_CONFIG_ENV, str(env_path))

  path = mapping_config_path_from_args(CliArgs())

  assert path == env_path


def test_mapping_config_path_from_args_uses_default_without_custom_path(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """The resolver should return None when the packaged default should be used."""
  monkeypatch.delenv(SYNC_LISTING_CONFIG_ENV, raising=False)

  assert mapping_config_path_from_args(CliArgs()) is None


def test_mapping_config_path_from_args_expands_cli_user_home(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """CLI --config paths should support user-home expansion."""
  home_dir = tmp_path / "home"
  home_dir.mkdir()
  monkeypatch.setenv("HOME", str(home_dir))

  path = mapping_config_path_from_args(CliArgs(config="~/mappings.toml"))

  assert path == home_dir / "mappings.toml"


def test_mapping_config_path_from_args_expands_env_user_home(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """SYNC_LISTING_CONFIG paths should support user-home expansion."""
  home_dir = tmp_path / "home"
  home_dir.mkdir()
  monkeypatch.setenv("HOME", str(home_dir))
  monkeypatch.setenv(SYNC_LISTING_CONFIG_ENV, "~/mappings.toml")

  path = mapping_config_path_from_args(CliArgs())

  assert path == home_dir / "mappings.toml"
