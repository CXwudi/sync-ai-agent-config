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
from dataclasses import dataclass
from datetime import datetime
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

  All relative paths are relative to the home directory.
  """
  relative_path: Path                      # e.g., ".claude/CLAUDE.md"
  # Windows specific relative path
  # e.g. Cline prompts folder in windows is "Documents/Cline/Rules/" where as in linux it is "Cline/Rules/"
  windows_relative_path: Optional[Path]
  keep_mode: KeepMode
  is_directory: bool = False
  description: str = ""


@dataclass
class RsyncTask:
  """Represents a single rsync operation with source, destination, and metadata."""
  src: Path               # Absolute source path
  dest: Path              # Absolute destination path
  description: str
  is_directory: bool = False


@dataclass
class Config:
  """Configuration for sync operations"""
  remote_user: str
  remote_host: str
  remote_base_dir: str
  windows_user: Optional[str]
  rsync_opts: List[str]

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
    remote_base_dir = args.remote_dir or os.getenv(
        'SYNC_DIR', '~/sync-files/ai-agents-related')
    windows_user = args.windows_user or os.getenv('WIN_USER')

    if not remote_user:
      raise ValueError("Remote user must be configured")
    if not remote_host:
      raise ValueError("Remote host must be configured")

    rsync_raw = getattr(args, 'rsync_opts', None)
    rsync_opts: List[str] = []
    if isinstance(rsync_raw, str):
      rsync_opts = rsync_raw.split()
    elif isinstance(rsync_raw, list):
      rsync_opts = [str(x) for x in cast(List[Any], rsync_raw)]

    return cls(
        remote_user=remote_user,
        remote_host=remote_host,
        remote_base_dir=remote_base_dir,
        windows_user=windows_user,
        rsync_opts=rsync_opts
    )

### File Mappings ###

ALL_FILE_MAPPINGS = [
  # Claude Code
  FileMapping(Path(".claude.json"), None, KeepMode.KEEP_BOTH,
              description="Claude config"),
  FileMapping(Path(".claude/CLAUDE.md"), None,
              KeepMode.PREFER_WINDOWS, description="Claude instructions"),
  FileMapping(Path(".claude/agents/"), None, KeepMode.PREFER_WINDOWS,
              is_directory=True, description="Claude agents"),

  # Gemini CLI
  FileMapping(Path(".gemini/settings.json"), None,
              KeepMode.KEEP_BOTH, description="Gemini settings"),
  FileMapping(Path(".gemini/GEMINI.md"), None,
              KeepMode.PREFER_WINDOWS, description="Gemini instructions"),

  # Codex
  FileMapping(Path(".codex/config.toml"), None,
              KeepMode.KEEP_BOTH, description="Codex config"),
  FileMapping(Path(".codex/AGENTS.md"), None,
              KeepMode.PREFER_WINDOWS, description="Codex agents"),

  # Cline
  FileMapping(Path(".vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"),
              Path("AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"),
              KeepMode.KEEP_BOTH, description="Cline MCP settings"),
  FileMapping(Path("Cline/Rules/"), Path("Documents/Cline/Rules/"),
              KeepMode.PREFER_WINDOWS, is_directory=True, description="Cline rules"),
]

### Core Logic ###

# TODO

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
  op_group.add_argument('--rsync-opts', default='-avz --update --delete --human-readable --mkpath',
                        help='Options to pass to rsync (default: "-avz --update --delete --human-readable --mkpath")')
  op_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                        help='Set logging level (default: INFO)')
  op_group.add_argument('--list', action='store_true',
                        help='List file mappings and exit')

  # Info options
  info_group = parser.add_argument_group('information options')
  info_group.add_argument('--version', action='version',
                          version='%(prog)s 3.0.0')

  return parser


def main() -> int:
  """Main function"""
  parser = create_argument_parser()
  args = parser.parse_args()

  # Configure log level based on CLI argument (second basicConfig call)
  numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
  logging.basicConfig(level=numeric_level, force=True)

  # Create config
  config = Config.from_args(args)

  logger.info("AI Config Sync")
  logger.debug("Configuration: %s", config)

  # TODO: menual DI that is enough to get file list
  # TODO: Implement file operations
  if args.list:
    logger.info("File mappings list requested")
    return 0

  if not args.operation:
    parser.error("Operation (push/pull) is required")

  logger.info("Start %s operation", args.operation.value)
  # TODO: complete the DI, only setup the classes for the cooresponding operation
  logger.info("Operation %s completed successfully", args.operation.value)
  return 0


if __name__ == '__main__':
  sys.exit(main())
