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

  `relative_path` is the default path relative to Linux home, Windows user dir,
  and the remote base directory.
  `linux_override_path` and `windows_override_path` can override the Linux or
  Windows path with either a relative path or a POSIX absolute path.
  `remote_relative_path` can override the remote path relative to the remote
  base directory.
  """

  model_config = ConfigDict(extra="forbid")

  relative_path: Path
  linux_override_path: Path | None = None
  windows_override_path: Path | None = None
  remote_relative_path: Path | None = None
  keep_mode: KeepMode
  is_directory: bool = Field(default=False, strict=True)
  description: str = ""

  @field_validator(
    "relative_path",
    "linux_override_path",
    "windows_override_path",
    "remote_relative_path",
    mode="before",
  )
  @classmethod
  def _validate_path_common(cls, value: object) -> object:
    """Reject empty, Windows drive-qualified, and parent-traversal paths."""
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

    path = Path(path_text)
    windows_path = PureWindowsPath(path_text)
    if windows_path.is_absolute() or windows_path.drive or path_text.startswith("\\"):
      raise ValueError(
        "Path values must not be Windows drive-qualified or backslash-rooted paths"
      )

    if ".." in path.parts or ".." in windows_path.parts:
      raise ValueError("Path values must not contain parent-directory (..) segments")

    return value

  @field_validator(
    "relative_path",
    "remote_relative_path",
    mode="before",
  )
  @classmethod
  def _validate_relative_only_path(cls, value: object) -> object:
    """Reject absolute paths for fields that must stay relative."""
    if value is None:
      return value

    if isinstance(value, str):
      path_text = value
    elif isinstance(value, Path):
      path_text = str(value)
    else:
      return value

    if Path(path_text).is_absolute():
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
