"""Data models for sync-ai-config."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Optional


class Operation(Enum):
  """Available sync operations."""

  PUSH = "push"
  PULL = "pull"


class KeepMode(Enum):
  """Mode of keeping files between Linux and Windows."""

  PREFER_WINDOWS = "prefer_windows"  # Windows→Linux→Remote
  PREFER_LINUX = "prefer_linux"  # Linux→Windows→Remote
  KEEP_BOTH = "keep_both"  # Windows→Remote(.windows) + Linux→Remote(.linux)


@dataclass
class FileMapping:
  """
  Windows, Linux, Remote, 3-way file mapping.

  For Windows and Linux, paths are relative to the home directory.
  For Remote, paths are relative to a remote directory specified in the config.
  """

  relative_path: Path
  windows_relative_path: Optional[Path]
  remote_relative_path: Optional[Path]
  keep_mode: KeepMode
  is_directory: bool = False
  description: str = ""

  def __iter__(self) -> Iterator[Any]:
    """Allow tuple unpacking of the mapping."""
    return iter(
      (
        self.relative_path,
        self.windows_relative_path,
        self.remote_relative_path,
        self.keep_mode,
        self.is_directory,
        self.description,
      )
    )


@dataclass
class RsyncTask:
  """A single rsync operation with source, destination, and metadata."""

  src: str | Path
  dest: str | Path
  description: str
  is_directory: bool = False
