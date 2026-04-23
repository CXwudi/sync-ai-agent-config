"""Data models for sync-ai-config."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PureWindowsPath

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Operation(Enum):
  """Available sync operations."""

  PUSH = "push"
  PULL = "pull"


class KeepMode(Enum):
  """Mode of keeping files between Linux and Windows."""

  PREFER_WINDOWS = "prefer_windows"  # Windows→Linux→Remote
  PREFER_LINUX = "prefer_linux"  # Linux→Windows→Remote
  KEEP_BOTH = "keep_both"  # Windows→Remote(.windows) + Linux→Remote(.linux)


class FileMapping(BaseModel):
  """
  Windows, Linux, Remote, 3-way file mapping.

  For Windows and Linux, paths are relative to the home directory.
  For Remote, paths are relative to a remote directory specified in the config.
  """

  model_config = ConfigDict(populate_by_name=True, extra="forbid")

  relative_path: Path = Field(alias="path")
  windows_relative_path: Path | None = Field(default=None, alias="windows_path")
  remote_relative_path: Path | None = Field(default=None, alias="remote_path")
  keep_mode: KeepMode
  is_directory: bool = Field(default=False, strict=True)
  description: str = ""

  @field_validator(
    "relative_path",
    "windows_relative_path",
    "remote_relative_path",
    mode="before",
  )
  @classmethod
  def _validate_relative_path_fragment(cls, value: object) -> object:
    """Reject empty and absolute path fragments before Path coercion."""
    if value is None:
      return value

    if isinstance(value, str):
      path_text = value
    elif isinstance(value, Path):
      path_text = str(value)
    else:
      return value

    if not path_text.strip():
      raise ValueError("Path values must not be empty")

    windows_path = PureWindowsPath(path_text)
    if (
      Path(path_text).is_absolute()
      or windows_path.is_absolute()
      or windows_path.drive
    ):
      raise ValueError("Path values must be relative path fragments")

    return value


class FileMappingConfig(BaseModel):
  """Config file containing sync file and directory mappings."""

  model_config = ConfigDict(extra="forbid")

  mappings: list[FileMapping]


@dataclass
class RsyncTask:
  """A single rsync operation with source, destination, and metadata."""

  src: str | Path
  dest: str | Path
  description: str
  is_directory: bool = False
