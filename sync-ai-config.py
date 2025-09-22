#!/usr/bin/env python3
"""
AI Configuration Sync Script
Syncs AI agent configuration files between local machine and remote server
"""

import argparse
import logging
import os
import subprocess
import sys
import shlex
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, cast

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

### Data Model ###


class Operation(Enum):
  """Available sync operations."""
  PUSH = "push"
  PULL = "pull"


class KeepMode(Enum):
  """Mode of keeping files between Linux and Windows"""
  PREFER_WINDOWS = "prefer_windows"  # Windows→Linux→Remote
  PREFER_LINUX = "prefer_linux"      # Linux→Windows→Remote
  # Windows→Remote(.windows) + Linux→Remote(.linux)
  KEEP_BOTH = "keep_both"


@dataclass
class FileMapping:
  """
  Windows, Linux, Remote, 3 way file mapping

  For Windows and Linux, the paths are relative to the home directory.
  For Remote, the paths are relative to a remote directory specified in the config.
  """
  relative_path: Path                      # e.g., ".claude/CLAUDE.md"
  # Windows specific relative path
  # e.g. Cline prompts folder in windows is "Documents/Cline/Rules/" where as in linux it is "Cline/Rules/"
  windows_relative_path: Optional[Path]
  keep_mode: KeepMode
  is_directory: bool = False
  description: str = ""

  def __iter__(self):
    """Allow tuple unpacking: relative_path, windows_relative_path, keep_mode, is_directory, description = mapping"""
    return iter((self.relative_path, self.windows_relative_path, self.keep_mode, self.is_directory, self.description))


@dataclass
class RsyncTask:
  """
  Represents a single rsync operation with source, destination, and metadata.

  The source and destination can be either a local path in Path object or a remote SSH/SFTP path in str
  """
  src: str | Path
  dest: str | Path
  description: str
  is_directory: bool = False


@dataclass
class Config:
  """Configuration for sync operations"""
  remote_user: str
  remote_host: str
  remote_base_dir: Path
  windows_user: Optional[str]
  rsync_opts: List[str]
  dry_run: bool

  @property
  def windows_user_dir(self) -> Optional[Path]:
    if not self.windows_user:
      return None
    return Path(f"/mnt/c/Users/{self.windows_user}")

  @property
  def local_home(self) -> Path:
    return Path.home()

  @property
  def remote_url(self) -> str:
    if not self.remote_user or not self.remote_host:
      raise ValueError("Remote user and host must be configured")
    return f"{self.remote_user}@{self.remote_host}"

  @classmethod
  def from_args(cls, args: argparse.Namespace) -> 'Config':
    """Create config from command line arguments with env var fallback

    Priority: Command line args > Environment variables > Defaults
    """
    # Resolve values with precedence: CLI > env > defaults
    remote_user = args.remote_user or os.getenv('SYNC_USER')
    remote_host = args.remote_host or os.getenv('SYNC_HOST')
    remote_base_dir = Path(args.remote_dir or os.getenv(
        'SYNC_DIR', '~/sync-files/ai-agents-related'))
    windows_user = args.windows_user or os.getenv('WIN_USER')

    if not remote_user:
      raise ValueError("Remote user must be configured")
    if not remote_host:
      raise ValueError("Remote host must be configured")

    rsync_raw = getattr(args, 'rsync_opts', None)
    rsync_opts: List[str] = []
    if isinstance(rsync_raw, str):
      rsync_opts = shlex.split(rsync_raw)
    elif isinstance(rsync_raw, list):
      rsync_opts = [str(x) for x in cast(List[Any], rsync_raw)]

    return cls(
        remote_user=remote_user,
        remote_host=remote_host,
        remote_base_dir=remote_base_dir,
        windows_user=windows_user,
        rsync_opts=rsync_opts,
        dry_run=args.dry_run
    )


### Constants ###
# File Mappings
ALL_FILE_MAPPINGS: List[FileMapping] = [
    # Claude Code
    FileMapping(Path(".claude.json"), None, KeepMode.KEEP_BOTH,
                description="Claude config"),
    FileMapping(Path(".claude/CLAUDE.md"), None,
                KeepMode.PREFER_WINDOWS, description="Claude prompt file"),
    FileMapping(Path(".claude/agents/"), None, KeepMode.PREFER_WINDOWS,
                is_directory=True, description="Claude subagents"),

    # Gemini CLI
    FileMapping(Path(".gemini/settings.json"), None,
                KeepMode.KEEP_BOTH, description="Gemini settings"),
    FileMapping(Path(".gemini/GEMINI.md"), None,
                KeepMode.PREFER_WINDOWS, description="Gemini prompt file"),

    # Codex
    FileMapping(Path(".codex/config.toml"), None,
                KeepMode.KEEP_BOTH, description="Codex config"),
    FileMapping(Path(".codex/AGENTS.md"), None,
                KeepMode.PREFER_WINDOWS, description="Codex prompt file"),

    # Cline
    FileMapping(Path(".vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"),
                Path("AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"),
                KeepMode.KEEP_BOTH, description="Cline MCP settings for VSCode"),
    # The windows path is dependent on the user's Documents folder location, not necessarily "Documents"
    # FileMapping(Path("Cline/Rules/"), Path("Documents/Cline/Rules/"),
    #             KeepMode.PREFER_WINDOWS, is_directory=True, description="Cline rules"),
]
# Default rsync options
DEFAULT_RSYNC_OPTS = '-avz --update --delete --human-readable --mkpath'
### Core Logic ###


class TaskBuilder:
  """Builds rsync tasks based on file mappings and keep mode"""

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
        # the pull logic is the same for both prefer modes
        # since only one file pushed to remote (the prefer one)
        tasks.extend(self._remote_to_linux_then_windows(mapping))
    logger.info("Built %d pull tasks", len(tasks))
    return tasks

  def _windows_to_linux_then_remote(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pushing Windows files to Linux then to remote."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      tasks.append(RsyncTask(
          src=self.config.windows_user_dir / windows_specific_relative_path,
          dest=linux_path,
          description=f"Windows to Linux: {description}",
          is_directory=is_directory
      ))

    tasks.append(RsyncTask(
        src=linux_path,
        dest=self._build_remote_path(relative_path),
        description=f"Linux to Remote: {description}",
        is_directory=is_directory
    ))
    return tasks

  def _linux_to_windows_then_remote(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pushing Linux files to Windows then to remote."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      tasks.append(RsyncTask(
          src=linux_path,
          dest=self.config.windows_user_dir / windows_specific_relative_path,
          description=f"Linux to Windows: {description}",
          is_directory=is_directory
      ))

    tasks.append(RsyncTask(
        src=linux_path,
        dest=self._build_remote_path(relative_path),
        description=f"Linux to Remote: {description}",
        is_directory=is_directory
    ))
    return tasks

  def _both_to_remote_separately(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pushing Linux and Windows files to remote separately."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []
    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      remote_relative_path_win = self._build_suffix_path(
          relative_path, ".windows")
      tasks.append(RsyncTask(
          src=self.config.windows_user_dir / windows_specific_relative_path,
          dest=self._build_remote_path(remote_relative_path_win),
          description=f"Windows to Remote: {description}",
          is_directory=is_directory
      ))

    remote_relative_path_linux = self._build_suffix_path(
        relative_path, ".linux")
    linux_path = self.config.local_home / relative_path
    tasks.append(RsyncTask(
        src=linux_path,
        dest=self._build_remote_path(remote_relative_path_linux),
        description=f"Linux to Remote: {description}",
        is_directory=is_directory
    ))

    return tasks

  def _remote_to_linux_then_windows(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pulling Linux files from remote then to Windows."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    tasks.append(RsyncTask(
        src=self._build_remote_path(relative_path),
        dest=linux_path,
        description=f"Remote to Linux: {description}",
        is_directory=is_directory
    ))

    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      tasks.append(RsyncTask(
          src=linux_path,
          dest=self.config.windows_user_dir / windows_specific_relative_path,
          description=f"Linux to Windows: {description}",
          is_directory=is_directory
      ))

    return tasks

  def _remote_separately_to_both(self, mapping: FileMapping) -> List[RsyncTask]:
    """Build tasks for pulling Linux and Windows files from remote separately."""
    relative_path = mapping.relative_path
    windows_relative_path = mapping.windows_relative_path
    description = mapping.description
    is_directory = mapping.is_directory

    tasks: List[RsyncTask] = []

    linux_path = self.config.local_home / relative_path
    remote_relative_path_linux = self._build_suffix_path(
        relative_path, ".linux")
    tasks.append(RsyncTask(
        src=self._build_remote_path(remote_relative_path_linux),
        dest=linux_path,
        description=f"Remote to Linux: {description}",
        is_directory=is_directory
    ))

    if self.config.windows_user_dir is not None:
      windows_specific_relative_path: Path = windows_relative_path or relative_path
      remote_relative_path_win = self._build_suffix_path(
          relative_path, ".windows")
      tasks.append(RsyncTask(
          src=self._build_remote_path(remote_relative_path_win),
          dest=self.config.windows_user_dir / windows_specific_relative_path,
          description=f"Remote to Windows: {description}",
          is_directory=is_directory
      ))

    return tasks

  def _build_remote_path(self, relative_path: Path) -> str:
    """Build remote path string for rsync destination."""
    return f"{self.config.remote_url}:{self.config.remote_base_dir / relative_path}"

  def _build_suffix_path(self, orig_path: Path, suffix: str) -> Path:
    """Build path with suffix added before extension"""
    name = orig_path.stem
    ext = orig_path.suffix
    return orig_path.parent / f"{name}{suffix}{ext}"


class TaskExecutor:
  """Executes rsync tasks"""

  def __init__(self, config: Config):
    self.config = config

  # TODO: return a dataclass for result
  def execute_tasks(self, tasks: List[RsyncTask]) -> None:
    """Execute all tasks"""
    logger.info("Executing %d tasks", len(tasks))
    for task in tasks:
      self._execute_one_task(task)
    if self.config.dry_run:
      logger.info("Dry run complete")

  def _execute_one_task(self, task: RsyncTask) -> bool:
    """Execute one task using rsync"""
    # Build the rsync command

    # Handle source and destination path
    src = str(task.src)  # convert Path to str
    dest = str(task.dest)

    if task.is_directory:
      if not src.endswith('/'):
        src += '/'
      if not dest.endswith('/'):
        dest += '/'

    # Build the rsync command
    cmd = ['rsync',
           *self.config.rsync_opts, 
           src, dest]

    # Log the execution
    logger.info("Executing for %s:\n%s", task.description, ' '.join(cmd))

    if self.config.dry_run:
      return True

    # Execute the command
    try:
      result = subprocess.run(
          cmd,
          capture_output=True,
          text=True,
          timeout=60,  # 1 minute timeout
          check=False
      )

      # Handle results
      if result.returncode == 0:
        logger.info("Success: %s", task.description)
        return True
      else:
        logger.error("Failed: %s - Return code: %d",
                     task.description, result.returncode)
        if result.stderr:
          logger.error("Error output: %s", result.stderr.strip())
        return False

    except subprocess.TimeoutExpired:
      logger.error("Timeout: %s", task.description)
      return False
    except Exception as e:
      logger.error("Exception executing %s: %s", task.description, e)
      return False

### Main ###


def create_argument_parser() -> argparse.ArgumentParser:
  """Create and configure the argument parser, TODO: need modification from newest design doc"""
  parser = argparse.ArgumentParser(
      description='Sync AI agent configuration files between local machine and remote server'
  )

  parser.add_argument('operation', nargs='?',
                      type=Operation,
                      choices=list(Operation),
                      help='Operation to perform')

# Remote configuration
  remote_group = parser.add_argument_group('remote configuration')
  remote_group.add_argument('-u', '--remote-user',
                            help='Remote SSH username (overrides SYNC_USER)')
  remote_group.add_argument('-H', '--remote-host',
                            help='Remote SSH host (overrides SYNC_HOST)')
  remote_group.add_argument('-d', '--remote-dir',
                            help='Remote directory path (overrides SYNC_DIR)')

  # Local configuration
  local_group = parser.add_argument_group('local configuration')
  local_group.add_argument('-w', '--windows-user',
                           help='Windows username (overrides WIN_USER, optional - enables Windows file sync)')

  # Operation options
  op_group = parser.add_argument_group('operation options')
  op_group.add_argument('--rsync-opts', default=DEFAULT_RSYNC_OPTS,
                        help=f'Options to pass to rsync (default: "{DEFAULT_RSYNC_OPTS}")')
  op_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                        help='Set logging level (default: INFO)')
  op_group.add_argument('--dry-run', action='store_true',
                        help='Dry run: List all rsync commands, not executing')

  # Info options
  info_group = parser.add_argument_group('information options')
  info_group.add_argument('--version', action='version',
                          version='%(prog)s 3.0.0')

  return parser


def main() -> int:
  """Main function"""
  parser = create_argument_parser()
  args = parser.parse_args()

  # Configure log level based on CLI argument
  numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
  logger.setLevel(numeric_level)

  # Check for rsync
  if not shutil.which('rsync'):
    logger.critical("'rsync' command not found. Please install rsync and ensure it is in your PATH.")
    return 1
  
  # Create config
  try:
    config = Config.from_args(args)
  except ValueError as e:
    parser.error(str(e))
    return 1

  logger.info("AI Config Sync")
  logger.debug("Configuration: %s", config)

  if not args.operation:
    parser.error("Operation (push/pull) is required")
    return 1

  # Manual DI
  task_builder = TaskBuilder(config)
  task_executor = TaskExecutor(config)

  # Build tasks
  logger.info("Building tasks for %s operation", args.operation.value)
  tasks: List[RsyncTask] = (
      task_builder.build_push_tasks(ALL_FILE_MAPPINGS) if args.operation == Operation.PUSH
      else task_builder.build_pull_tasks(ALL_FILE_MAPPINGS)
  )
  logger.debug("Built Tasks: %s", tasks)

  # Execute tasks
  logger.info("Starting %s operation", args.operation.value)
  task_executor.execute_tasks(tasks)

  return 0


if __name__ == '__main__':
  sys.exit(main())
