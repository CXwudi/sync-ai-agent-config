"""Configuration models for sync-ai-config."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Config:
  """Configuration for sync operations."""

  remote_user: str
  remote_host: str
  remote_base_dir: Path
  windows_user: Optional[str]
  rsync_opts: List[str]
  dry_run: bool

  @property
  def windows_user_dir(self) -> Optional[Path]:
    """Return the Windows user directory path when configured."""
    if not self.windows_user:
      return None
    return Path(f"/mnt/c/Users/{self.windows_user}")

  @property
  def local_home(self) -> Path:
    """Return the local home directory path."""
    return Path.home()

  @property
  def remote_url(self) -> str:
    """
    Return the remote SSH URL, e.g., user@host.

    Raises:
      ValueError: If remote user or host is not set.
    """
    if not self.remote_user or not self.remote_host:
      raise ValueError("Remote user and host must be configured")
    return f"{self.remote_user}@{self.remote_host}"
