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
from typing import List, Optional

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ANSI color codes


class Operation(Enum):
  PUSH = "push"
  PULL = "pull"


@dataclass
class Config:
  """Configuration for sync operations"""
  remote_user: Optional[str]
  remote_host: Optional[str]
  remote_base_dir: str
  windows_user: Optional[str]

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
    return cls(
        remote_user=args.remote_user or os.getenv('SYNC_USER'),
        remote_host=args.remote_host or os.getenv('SYNC_HOST'),
        remote_base_dir=args.remote_dir or os.getenv(
            'SYNC_DIR', '~/sync-files/ai-agents-related'),
        windows_user=args.windows_user or os.getenv('WIN_USER')
    )


def create_argument_parser() -> argparse.ArgumentParser:
  """Create and configure the argument parser, TODO: need modification from newest design doc"""
  parser = argparse.ArgumentParser(
      description='Sync AI agent configuration files between local machine and remote server'
  )

  parser.add_argument('operation', nargs='?',
                      type=lambda x: Operation(x),
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
                          version='%(prog)s 2.5.0')

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

  logger.info("AI Config Sync - Starting %s operation",
              args.operation.value if args.operation else "info")
  logger.debug("Configuration: %s", config)

  # TODO: Implement file operations
  if args.list:
    logger.info("File mappings list requested")
    return 0

  if not args.operation:
    parser.error("Operation (push/pull) is required")

  logger.info("Operation %s completed successfully", args.operation.value)
  return 0


if __name__ == '__main__':
  sys.exit(main())
