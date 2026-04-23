"""Load sync file mapping configuration from TOML resources and files."""

from __future__ import annotations

import tomllib
from importlib import resources
from pathlib import Path

from pydantic import ValidationError

from sync_ai_config.models import FileMapping, FileMappingConfig


DEFAULT_MAPPINGS_RESOURCE = "default_mappings.toml"
SYNC_CONFIG_ENV = "SYNC_CONFIG"


class MappingConfigError(ValueError):
  """Raised when sync mapping config cannot be read or validated."""


def read_default_mappings_text() -> str:
  """Read the packaged default mapping config."""
  try:
    return (
      resources.files("sync_ai_config")
      .joinpath(DEFAULT_MAPPINGS_RESOURCE)
      .read_text(encoding="utf-8")
    )
  except OSError as exc:
    raise MappingConfigError(
      f"Failed to read packaged default mapping config {DEFAULT_MAPPINGS_RESOURCE!r}: {exc}"
    ) from exc


def load_default_mappings() -> list[FileMapping]:
  """Load the packaged default sync file mappings."""
  return _parse_mappings_toml(
    read_default_mappings_text(),
    source=f"packaged default {DEFAULT_MAPPINGS_RESOURCE!r}",
  )


def load_mappings_from_path(path: Path) -> list[FileMapping]:
  """Load sync file mappings from a custom TOML file path."""
  config_path = path.expanduser()
  try:
    text = config_path.read_text(encoding="utf-8")
  except OSError as exc:
    raise MappingConfigError(
      f"Failed to read mapping config file {config_path}: {exc}"
    ) from exc

  return _parse_mappings_toml(text, source=f"mapping config file {config_path}")


def load_mappings(config_path: Path | None = None) -> list[FileMapping]:
  """Load sync file mappings from a custom path or the packaged default."""
  if config_path is None:
    return load_default_mappings()
  return load_mappings_from_path(config_path)


def _parse_mappings_toml(text: str, *, source: str) -> list[FileMapping]:
  """Parse TOML text into validated file mappings."""
  try:
    data = tomllib.loads(text)
  except tomllib.TOMLDecodeError as exc:
    raise MappingConfigError(f"Invalid TOML in {source}: {exc}") from exc

  try:
    return FileMappingConfig.model_validate(data).mappings
  except ValidationError as exc:
    raise MappingConfigError(
      f"Invalid mapping config schema in {source}:\n{exc}"
    ) from exc
