"""Default mapping constants and compatibility exports for sync-ai-config."""

from __future__ import annotations

import tomllib
from importlib import resources

from sync_ai_config.models import FileMapping, FileMappingConfig


DEFAULT_MAPPINGS_RESOURCE = "default_mappings.toml"
DEFAULT_RSYNC_OPTS = "-avzL --update --delete --human-readable --mkpath"


def read_default_mappings_text() -> str:
  """Read the packaged default mapping config."""
  return (
    resources.files("sync_ai_config")
    .joinpath(DEFAULT_MAPPINGS_RESOURCE)
    .read_text(encoding="utf-8")
  )


def load_default_file_mappings() -> list[FileMapping]:
  """Load the packaged default sync file mappings."""
  data = tomllib.loads(read_default_mappings_text())
  return FileMappingConfig.model_validate(data).mappings


ALL_FILE_MAPPINGS: list[FileMapping] = load_default_file_mappings()
