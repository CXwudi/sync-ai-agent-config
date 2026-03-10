"""Build rsync tasks based on file mappings and keep mode."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from sync_ai_config.config import Config
from sync_ai_config.models import FileMapping, KeepMode, RsyncTask


logger = logging.getLogger(__name__)


class TaskBuilder:
  """Builds rsync tasks based on file mappings and keep mode."""

  def __init__(self, config: Config):
    self.config = config

  def build_push_tasks(self, mappings: List[FileMapping]) -> List[RsyncTask]:
    """Build rsync tasks for pushing files from local to remote."""
    tasks: List[RsyncTask] = []
    logger.info("Building push tasks for %d mappings", len(mappings))
    for mapping in mappings:
      if mapping.keep_mode == KeepMode.PREFER_WINDOWS:
        tasks.extend(self._windows_to_linux_then_remote(mapping))
      elif mapping.keep_mode == KeepMode.PREFER_LINUX:
        tasks.extend(self._linux_to_windows_then_remote(mapping))
      elif mapping.keep_mode == KeepMode.KEEP_BOTH:
        tasks.extend(self._both_to_remote_separately(mapping))
    logger.info("Built %d push tasks", len(tasks))
    return tasks

  def build_pull_tasks(self, mappings: List[FileMapping]) -> List[RsyncTask]:
    """Build rsync tasks for pulling files from remote to local."""
    tasks: List[RsyncTask] = []
    logger.info("Building pull tasks for %d mappings", len(mappings))
    for mapping in mappings:
      if mapping.keep_mode == KeepMode.KEEP_BOTH:
        tasks.extend(self._remote_separately_to_both(mapping))
      elif mapping.keep_mode in (KeepMode.PREFER_WINDOWS, KeepMode.PREFER_LINUX):
        # The pull logic is the same for both prefer modes since only one file is pushed to remote.
        tasks.extend(self._remote_to_linux_then_windows(mapping))
    logger.info("Built %d pull tasks", len(tasks))
    return tasks

  def _windows_to_linux_then_remote(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pushing Windows files to Linux then to remote."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    remote_relative_path = mapping.remote_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      tasks.append(
        RsyncTask(
          src=self.config.windows_user_dir / windows_specific_relative_path,
          dest=linux_path,
          description=f"Windows to Linux: {description}",
          is_directory=is_directory,
        )
      )

    tasks.append(
      RsyncTask(
        src=linux_path,
        dest=self._build_remote_path(relative_path, remote_relative_path),
        description=f"Linux to Remote: {description}",
        is_directory=is_directory,
      )
    )
    return tasks

  def _linux_to_windows_then_remote(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pushing Linux files to Windows then to remote."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    remote_relative_path = mapping.remote_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      tasks.append(
        RsyncTask(
          src=linux_path,
          dest=self.config.windows_user_dir / windows_specific_relative_path,
          description=f"Linux to Windows: {description}",
          is_directory=is_directory,
        )
      )

    tasks.append(
      RsyncTask(
        src=linux_path,
        dest=self._build_remote_path(relative_path, remote_relative_path),
        description=f"Linux to Remote: {description}",
        is_directory=is_directory,
      )
    )
    return tasks

  def _both_to_remote_separately(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pushing Linux and Windows files to remote separately."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    remote_relative_path = mapping.remote_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []
    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      base_remote_path = remote_relative_path if remote_relative_path else relative_path
      remote_relative_path_win = self._build_suffix_path(base_remote_path, ".windows")
      tasks.append(
        RsyncTask(
          src=self.config.windows_user_dir / windows_specific_relative_path,
          dest=self._build_remote_path(remote_relative_path_win),
          description=f"Windows to Remote: {description}",
          is_directory=is_directory,
        )
      )

    base_remote_path = remote_relative_path if remote_relative_path else relative_path
    remote_relative_path_linux = self._build_suffix_path(base_remote_path, ".linux")
    linux_path = self.config.local_home / relative_path
    tasks.append(
      RsyncTask(
        src=linux_path,
        dest=self._build_remote_path(remote_relative_path_linux),
        description=f"Linux to Remote: {description}",
        is_directory=is_directory,
      )
    )

    return tasks

  def _remote_to_linux_then_windows(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pulling Linux files from remote then to Windows."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    remote_relative_path = mapping.remote_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    tasks.append(
      RsyncTask(
        src=self._build_remote_path(relative_path, remote_relative_path),
        dest=linux_path,
        description=f"Remote to Linux: {description}",
        is_directory=is_directory,
      )
    )

    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      tasks.append(
        RsyncTask(
          src=linux_path,
          dest=self.config.windows_user_dir / windows_specific_relative_path,
          description=f"Linux to Windows: {description}",
          is_directory=is_directory,
        )
      )

    return tasks

  def _remote_separately_to_both(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pulling Linux and Windows files from remote separately."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    remote_relative_path = mapping.remote_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    base_remote_path = remote_relative_path if remote_relative_path else relative_path
    remote_relative_path_linux = self._build_suffix_path(base_remote_path, ".linux")
    tasks.append(
      RsyncTask(
        src=self._build_remote_path(remote_relative_path_linux),
        dest=linux_path,
        description=f"Remote to Linux: {description}",
        is_directory=is_directory,
      )
    )

    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      base_remote_path = remote_relative_path if remote_relative_path else relative_path
      remote_relative_path_win = self._build_suffix_path(base_remote_path, ".windows")
      tasks.append(
        RsyncTask(
          src=self._build_remote_path(remote_relative_path_win),
          dest=self.config.windows_user_dir / windows_specific_relative_path,
          description=f"Remote to Windows: {description}",
          is_directory=is_directory,
        )
      )

    return tasks

  def _build_remote_path(
    self, relative_path: Path, custom_relative_path: Optional[Path] = None
  ) -> str:
    """
    Build remote path string for rsync destination.

    Args:
      relative_path: Default path to use if custom_relative_path is not provided.
      custom_relative_path: Optional custom path to override the default remote path.

    Returns:
      Remote path string in format user@host:path.
    """
    base_remote_relative_path = (
      custom_relative_path if custom_relative_path else relative_path
    )
    return f"{self.config.remote_url}:{self.config.remote_base_dir / base_remote_relative_path}"

  def _build_suffix_path(self, orig_path: Path, suffix: str) -> Path:
    """Build a path with a suffix added before the extension."""
    name = orig_path.stem
    ext = orig_path.suffix
    return orig_path.parent / f"{name}{suffix}{ext}"
