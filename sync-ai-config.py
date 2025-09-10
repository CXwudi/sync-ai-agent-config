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

# ANSI color codes


class Colors:
  RED = '\033[0;31m'
  GREEN = '\033[0;32m'
  YELLOW = '\033[1;33m'
  BLUE = '\033[0;34m'
  NC = '\033[0m'  # No Color


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


@dataclass
class FileMapping:
  """Represents a file or directory sync mapping"""
  local_path: Path
  remote_name: str
  description: str
  is_directory: bool = False


class ColoredFormatter(logging.Formatter):
  """Custom formatter with colors"""

  COLORS = {
      'DEBUG': Colors.BLUE,
      'INFO': Colors.BLUE,
      'WARNING': Colors.YELLOW,
      'ERROR': Colors.RED,
      'CRITICAL': Colors.RED,
  }

  def format(self, record: logging.LogRecord):
    log_color = self.COLORS.get(record.levelname, Colors.NC)

    # Add symbols for different levels
    symbols = {
        'DEBUG': 'ℹ',
        'INFO': 'ℹ',
        'WARNING': '⚠',
        'ERROR': '✗',
        'CRITICAL': '✗',
    }

    symbol = symbols.get(record.levelname, '')
    record.symbol = symbol

    # Format the message with color
    original_msg = record.msg
    record.msg = f"{log_color}{symbol} {original_msg}{Colors.NC}"
    result = super().format(record)
    record.msg = original_msg  # Reset for file handler

    return result


class LoggingService:
  """Handles all logging configuration and setup"""

  def __init__(self, name: str, verbose: bool = False, quiet: bool = False):
    self.logger = self._setup_logger(name, verbose, quiet)

  def get_logger(self) -> logging.Logger:
    """Get the configured logger instance"""
    return self.logger

  def _setup_logger(self, name: str, verbose: bool, quiet: bool) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger(name)

    # Set log level based on verbosity/quiet
    if quiet:
      logger.setLevel(logging.WARNING)
    elif verbose:
      logger.setLevel(logging.DEBUG)
    else:
      logger.setLevel(logging.INFO)

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter('%(message)s'))
    logger.addHandler(console_handler)

    # File handler
    log_file = Path.home() / '.sync-ai-config.log'
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


class ProgressReporter:
  """Handles user interface and progress reporting"""

  def __init__(self, logger: logging.Logger):
    self.logger = logger
    self.success_count = 0
    self.fail_count = 0

  def track_success(self) -> None:
    """Track successful operation"""
    self.success_count += 1

  def track_failure(self) -> None:
    """Track failed operation"""
    self.fail_count += 1

  def print_summary(self, operation: str, dry_run: bool = False) -> None:
    """Print operation summary"""
    self.logger.info("═" * 50)
    self.logger.info(
        "%s Summary: %d succeeded, %d failed", operation, self.success_count, self.fail_count
    )

    if dry_run:
      self.logger.info(
          "Dry run completed - no files were actually transferred")

  def show_config(self, config: Config) -> None:
    """Show current configuration"""
    self.logger.info("Current Configuration:")
    self.logger.info("═" * 50)
    self.logger.info("  Remote User: %s", config.remote_user)
    self.logger.info("  Remote Host: %s", config.remote_host)
    self.logger.info("  Remote Dir:  %s", config.remote_base_dir)
    self.logger.info("  Windows User: %s",
                     config.windows_user or "Not configured")
    win_dir = config.windows_user_dir
    self.logger.info("  Windows Dir: %s",
                     win_dir if win_dir else "Not configured")
    self.logger.info("═" * 50)

  def list_mappings(self, mappings: List[FileMapping], config: Config) -> None:
    """List all file mappings"""
    self.logger.info("File Mappings:")
    self.logger.info("═" * 50)

    for mapping in mappings:
      status = "✓" if mapping.local_path.exists() else "✗"
      print(f"  [{status}] {mapping.local_path}")
      print(f"      → {config.remote_base_dir}/{mapping.remote_name}")
      print()

  def reset_counters(self) -> None:
    """Reset success and failure counters"""
    self.success_count = 0
    self.fail_count = 0


class FileMappingProvider:
  """Provides file mapping configurations based on system setup"""

  def __init__(self, config: Config):
    self.config = config

  def get_local_to_remote_mappings(self) -> List[FileMapping]:
    """Create file mappings for sync operations"""
    c = self.config

    mappings = [
        FileMapping(
            c.local_home / '.claude.json',
            '.claude.linux.json',
            'Claude Linux config'
        ),
        FileMapping(
            c.local_home / '.claude' / 'CLAUDE.md',
            '.claude/CLAUDE.md',
            'CLAUDE.md (Linux)'
        ),
        FileMapping(
            c.local_home / '.claude' / 'agents',
            '.claude/agents/',
            'Claude agents directory (Linux)',
            is_directory=True
        ),
        FileMapping(
            c.local_home / '.gemini' / 'settings.json',
            '.gemini/settings.linux.json',
            'Gemini Linux settings'
        ),
        FileMapping(
            c.local_home / '.gemini' / 'GEMINI.md',
            '.gemini/GEMINI.md',
            'GEMINI.md (Linux)'
        ),
    ]

    # Add Windows mappings only if Windows username is configured
    if c.windows_user and c.windows_user_dir:
      win_dir = c.windows_user_dir
      mappings.extend([
          FileMapping(
              win_dir / '.claude.json',
              '.claude.windows.json',
              'Claude Windows config'
          ),
          FileMapping(
              win_dir / '.claude' / 'CLAUDE.md',
              '.claude/CLAUDE.md',
              'CLAUDE.md (Windows)'
          ),
          FileMapping(
              win_dir / '.claude' / 'agents',
              '.claude/agents/',
              'Claude agents directory (Windows)',
              is_directory=True
          ),
          FileMapping(
              win_dir / '.gemini' / 'settings.json',
              '.gemini/settings.windows.json',
              'Gemini Windows settings'
          ),
          FileMapping(
              win_dir / '.gemini' / 'GEMINI.md',
              '.gemini/GEMINI.md',
              'GEMINI.md (Windows)'
          ),
      ])

    # Add script itself
    script_path = Path(__file__).resolve()
    mappings.append(
        FileMapping(
            script_path,
            script_path.name,
            'Sync script'
        )
    )

    return mappings

  def get_windows_to_linux_mappings(self) -> List[FileMapping]:
    """Create Windows to Linux file mappings for local rsync operations"""
    if not self.config.windows_user or not self.config.windows_user_dir:
      return []

    win_dir = self.config.windows_user_dir
    return [
        FileMapping(
            win_dir / '.claude' / 'CLAUDE.md',
            str(self.config.local_home / '.claude' / 'CLAUDE.md'),
            'CLAUDE.md from Windows to Linux'
        ),
        FileMapping(
            win_dir / '.gemini' / 'GEMINI.md',
            str(self.config.local_home / '.gemini' / 'GEMINI.md'),
            'GEMINI.md from Windows to Linux'
        ),
        FileMapping(
            win_dir / '.claude' / 'agents',
            str(self.config.local_home / '.claude' / 'agents'),
            'Claude agents from Windows to Linux',
            is_directory=True
        ),
    ]


class RemoteOperations:
  """Handles all remote server interactions via SSH and rsync"""

  def __init__(self, config: Config, rsync_opts: List[str], logger: logging.Logger):
    self.config = config
    self.rsync_opts = rsync_opts
    self.logger = logger

  def check_connectivity(self) -> bool:
    """Check SSH connectivity to remote server"""
    self.logger.info("Checking SSH connectivity to %s...",
                     self.config.remote_url)

    try:
      result = subprocess.run(
          ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes',
           self.config.remote_url, 'echo', 'Connected'],
          capture_output=True,
          text=True,
          timeout=10
      )

      if result.returncode == 0:
        self.logger.info("%s✓ SSH connection successful%s",
                         Colors.GREEN, Colors.NC)
        return True
      else:
        self.logger.error("Cannot connect to %s", self.config.remote_url)
        return False

    except subprocess.TimeoutExpired:
      self.logger.error("Connection timeout to %s", self.config.remote_url)
      return False
    except Exception as e:
      self.logger.error("Connection error: %s", e)
      return False

  def ensure_remote_directory(self, path: str) -> bool:
    """Setup remote directory structure"""
    self.logger.info("Setting up remote directory structure...")

    try:
      subprocess.run(
          ['ssh', self.config.remote_url, f'mkdir -p {path}'],
          check=True,
          capture_output=True
      )
      return True
    except subprocess.CalledProcessError as e:
      self.logger.warning("Failed to create remote directory: %s", e)
      return False

  def sync_file(self, source: str, dest: str, description: str, is_directory: bool = False) -> bool:
    """Execute rsync for a single file or directory"""
    self.logger.info("Syncing %s", description)
    self.logger.debug("  From: %s", source)
    self.logger.debug("  To: %s", dest)

    try:
      cmd = ['rsync'] + self.rsync_opts.copy()

      # Add recursive flag for directories
      if is_directory:
        if '-r' not in cmd:
          cmd.append('-r')
        # Ensure source ends with / for directory sync
        if not source.endswith('/'):
          source += '/'

      cmd.extend([source, dest])
      result = subprocess.run(cmd, capture_output=True, text=True)

      if '--verbose' in self.rsync_opts and result.stdout:
        print(result.stdout)

      if result.returncode == 0:
        self.logger.info("%s✓ Synced %s%s", Colors.GREEN,
                         description, Colors.NC)
        return True
      else:
        self.logger.error("Failed to sync %s: %s", description, result.stderr)
        return False

    except Exception as e:
      self.logger.error("Error syncing %s: %s", description, e)
      return False


class LocalFileOperations:
  """Handles local file system operations"""

  def __init__(self, logger: logging.Logger):
    self.logger = logger

  def ensure_directory(self, file_path: Path) -> None:
    """Ensure local directory exists"""
    dir_path = file_path.parent
    if not dir_path.exists():
      self.logger.debug("Creating directory: %s", dir_path)
      dir_path.mkdir(parents=True, exist_ok=True)

  def file_exists(self, path: Path) -> bool:
    """Check if file exists"""
    return path.exists()


class BackupManager:
  """Manages backup operations for both local and remote files"""

  def __init__(self, config: Config, remote_ops: RemoteOperations,
               local_ops: LocalFileOperations, logger: logging.Logger):
    self.config = config
    self.remote_ops = remote_ops
    self.local_ops = local_ops
    self.logger = logger

  def create_remote_backup(self) -> bool:
    """Create backup on remote server"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"{self.config.remote_base_dir}/backups/{timestamp}"
    self.logger.info("Creating remote backup at %s...", backup_dir)

    try:
      subprocess.run(
          ['ssh', self.config.remote_url,
           f"mkdir -p {backup_dir} && "
           f"cp {self.config.remote_base_dir}/*.json "
           f"{self.config.remote_base_dir}/*.md "
           f"{self.config.remote_base_dir}/*.py "
           f"{self.config.remote_base_dir}/*.sh "
           f"{backup_dir}/ 2>/dev/null || true"],
          shell=False,
          capture_output=True
      )
      self.logger.info("%s✓ Remote backup created%s", Colors.GREEN, Colors.NC)
      return True
    except Exception as e:
      self.logger.warning("Backup failed: %s", e)
      return False

  def create_local_backup(self, mappings: List[FileMapping]) -> bool:
    """Create backup of local files"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = self.config.local_home / '.ai-config-backups' / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    self.logger.info("Creating local backup at %s...", backup_dir)

    success = True
    for mapping in mappings:
      if mapping.local_path.exists():
        try:
          dest_path = backup_dir / mapping.local_path.name
          import shutil
          shutil.copy2(mapping.local_path, dest_path)
        except Exception as e:
          self.logger.warning("Failed to backup %s: %s", mapping.local_path, e)
          success = False

    if success:
      self.logger.info("%s✓ Local backup created%s", Colors.GREEN, Colors.NC)
    return success


class PushOperation:
  """Handles push operation (local → remote)"""

  def __init__(self, config: Config, logger: logging.Logger, progress_reporter: ProgressReporter,
               file_mapping_provider: FileMappingProvider, remote_ops: RemoteOperations,
               local_ops: LocalFileOperations, dry_run: bool = False):
    self.config = config
    self.logger = logger
    self.progress_reporter = progress_reporter
    self.file_mapping_provider = file_mapping_provider
    self.remote_ops = remote_ops
    self.local_ops = local_ops
    self.dry_run = dry_run

  def filter_mappings(self, mappings: List[FileMapping]) -> List[FileMapping]:
    """Filter out Windows files that should be synced from Linux copies"""
    if not self.config.windows_user_dir:
      return mappings

    # Files to skip because they're synced from Linux copies
    skip_paths = {
        self.config.windows_user_dir / '.claude' / 'CLAUDE.md',
        self.config.windows_user_dir / '.gemini' / 'GEMINI.md',
        self.config.windows_user_dir / '.claude' / 'agents'
    }

    return [mapping for mapping in mappings if mapping.local_path not in skip_paths]

  def get_all_push_mappings(self) -> List[FileMapping]:
    """Get combined Windows-to-Linux and filtered local-to-remote mappings for push operation"""
    all_mappings: List[FileMapping] = []

    # Add Windows-to-Linux mappings with operation_type
    windows_to_linux_mappings = self.file_mapping_provider.get_windows_to_linux_mappings()
    for mapping in windows_to_linux_mappings:
      mapping.operation_type = "windows_to_linux"
      all_mappings.append(mapping)

    # Add filtered local-to-remote mappings with operation_type
    local_to_remote_mappings = self.file_mapping_provider.get_local_to_remote_mappings()
    filtered_mappings = self.filter_mappings(local_to_remote_mappings)
    for mapping in filtered_mappings:
      mapping.operation_type = "local_to_remote"
      all_mappings.append(mapping)

    return all_mappings

  def execute(self) -> bool:
    """Execute push operation"""
    self.logger.info("Starting PUSH operation (local → remote)...")
    self.progress_reporter.reset_counters()

    # Get all push mappings (Windows-to-Linux and filtered local-to-remote)
    all_mappings = self.get_all_push_mappings()

    # Process all mappings in single unified loop
    for mapping in all_mappings:
      if not self.local_ops.file_exists(mapping.local_path):
        if mapping.operation_type == "windows_to_linux":
          self.logger.warning("Windows file not found: %s", mapping.local_path)
        else:
          self.logger.warning("File not found: %s", mapping.local_path)
        self.progress_reporter.track_failure()
        continue

      # Determine destination path based on operation type
      dest_path = mapping.remote_name if mapping.operation_type == "windows_to_linux" else f"{self.config.remote_url}:{self.config.remote_base_dir}/{mapping.remote_name}"

      # Perform sync operation
      if self.remote_ops.sync_file(str(mapping.local_path), dest_path, mapping.description, mapping.is_directory):
        self.progress_reporter.track_success()
      else:
        self.progress_reporter.track_failure()

    self.progress_reporter.print_summary("Push", self.dry_run)
    return self.progress_reporter.fail_count == 0


class PullOperation:
  """Handles pull operation (remote → local)"""

  def __init__(self, config: Config, logger: logging.Logger, progress_reporter: ProgressReporter,
               file_mapping_provider: FileMappingProvider, remote_ops: RemoteOperations,
               local_ops: LocalFileOperations, dry_run: bool = False):
    self.config = config
    self.logger = logger
    self.progress_reporter = progress_reporter
    self.file_mapping_provider = file_mapping_provider
    self.remote_ops = remote_ops
    self.local_ops = local_ops
    self.dry_run = dry_run

  def get_pull_mappings(self) -> List[FileMapping]:
    """Get filtered FileMapping list for pull operations"""
    all_mappings = self.file_mapping_provider.get_local_to_remote_mappings()

    # Filter out script file (not pulled from remote)
    pull_mappings = [
        mapping for mapping in all_mappings
        if mapping.description != 'Sync script'
    ]

    return pull_mappings

  def execute(self) -> bool:
    """Execute pull operation"""
    self.logger.info("Starting PULL operation (remote → local)...")
    self.progress_reporter.reset_counters()

    pull_mappings = self.get_pull_mappings()

    for mapping in pull_mappings:
      if mapping.is_directory:
        # For directories, ensure the parent directory exists
        self.local_ops.ensure_directory(
            mapping.local_path.parent / mapping.local_path.name)
      else:
        # For files, ensure the directory exists
        self.local_ops.ensure_directory(mapping.local_path)

      remote_file = f"{self.config.remote_base_dir}/{mapping.remote_name}"
      remote_path = f"{self.config.remote_url}:{remote_file}"

      if self.remote_ops.sync_file(remote_path, str(mapping.local_path), mapping.description, mapping.is_directory):
        self.progress_reporter.track_success()
      else:
        self.progress_reporter.track_failure()

    self.progress_reporter.print_summary("Pull", self.dry_run)
    return self.progress_reporter.fail_count == 0


def create_argument_parser() -> argparse.ArgumentParser:
  """Create and configure the argument parser"""
  parser = argparse.ArgumentParser(
      description='Sync AI agent configuration files between local machine and remote server',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
EXAMPLES:
  %(prog)s push                       # Push configs to remote
  %(prog)s pull                       # Pull configs from remote
  %(prog)s -n push                    # Dry run push
  %(prog)s -vb pull                   # Verbose pull with backup
  %(prog)s --list                     # List file mappings
  %(prog)s --config                   # Show current configuration

  # With custom settings (override env vars)
  %(prog)s --remote-user username --remote-host server.example.com push
  %(prog)s --windows-user myuser pull
  %(prog)s -u username -H 192.168.1.100 -d ~/configs push

CONFIGURATION PRIORITY:
  Command line arguments > Environment variables > Required

ENVIRONMENT VARIABLES:
  SYNC_USER    Remote username (required if not specified via --remote-user)
  SYNC_HOST    Remote host (required if not specified via --remote-host)
  SYNC_DIR     Remote directory (default: ~/sync-files/ai-agents-related)
  WIN_USER     Windows username (optional - enables Windows file operations)
    """
  )

  parser.add_argument('operation', nargs='?',
                      choices=['push', 'pull'],
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
                           help='Windows username (optional - enables Windows file sync)')

  # Operation options
  op_group = parser.add_argument_group('operation options')
  op_group.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
  op_group.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress non-error output')
  op_group.add_argument('-n', '--dry-run', action='store_true',
                        help='Perform a dry run (show what would be synced)')
  op_group.add_argument('-b', '--backup', action='store_true',
                        help='Create timestamped backup before syncing')

  # Info options
  info_group = parser.add_argument_group('information options')
  info_group.add_argument('-c', '--check', action='store_true',
                          help='Only check connectivity')
  info_group.add_argument('-l', '--list', action='store_true',
                          help='List all file mappings')
  info_group.add_argument('--config', action='store_true',
                          help='Show current configuration')
  info_group.add_argument('--version', action='version',
                          version='%(prog)s 2.5.0')

  return parser


def main():
  parser = create_argument_parser()
  args = parser.parse_args()

  # Validate quiet and verbose are not both set
  if args.quiet and args.verbose:
    parser.error("--quiet and --verbose are mutually exclusive")

  # Initialize configuration from args (with env var fallback)
  config = Config.from_args(args)

  # Validate operation is provided (unless info-only operations)
  if not (args.list or args.config or args.check):
    if not args.operation:
      parser.error("Operation (push/pull) is required")

  # Validate required configuration (skip for info-only operations)
  if not (args.list or args.config):
    missing_params: List[str] = []
    if not config.remote_user:
      missing_params.append(
          "remote username (use --remote-user or set SYNC_USER)")
    if not config.remote_host:
      missing_params.append("remote host (use --remote-host or set SYNC_HOST)")

    if missing_params:
      parser.error(
          f"Missing required configuration: {', '.join(missing_params)}")

  # Initialize services
  logging_service = LoggingService(
      'sync-ai-config', verbose=args.verbose, quiet=args.quiet)
  logger = logging_service.get_logger()
  progress_reporter = ProgressReporter(logger)
  file_mapping_provider = FileMappingProvider(config)

  # Rsync options
  rsync_opts = ['-az', '--update', '--stats', '--human-readable', '--mkpath']
  if args.verbose:
    rsync_opts.extend(['-v', '--progress'])
  if args.quiet:
    rsync_opts.append('-q')
  if args.dry_run:
    rsync_opts.append('--dry-run')

  remote_ops = RemoteOperations(config, rsync_opts, logger)
  local_ops = LocalFileOperations(logger)
  backup_manager = BackupManager(config, remote_ops, local_ops, logger)

  # Initialize operation classes
  push_operation = PushOperation(config, logger, progress_reporter, file_mapping_provider,
                                 remote_ops, local_ops, args.dry_run)
  pull_operation = PullOperation(config, logger, progress_reporter, file_mapping_provider,
                                 remote_ops, local_ops, args.dry_run)

  try:
    # Show config if requested
    if args.config:
      progress_reporter.show_config(config)
      return 0

    # List mappings if requested
    if args.list:
      mappings = file_mapping_provider.get_local_to_remote_mappings()
      progress_reporter.list_mappings(mappings, config)
      return 0

    # Print header
    if not args.quiet:
      logger.info("═" * 50)
      logger.info("AI Config Sync Started")
      logger.info("Operation: %s", args.operation.upper())
      logger.info("Remote: %s", config.remote_url)
      logger.info("Remote Dir: %s", config.remote_base_dir)
      logger.info("Windows User: %s", config.windows_user)

    # Check connectivity
    if not remote_ops.check_connectivity():
      return 1

    # Check only mode
    if args.check:
      logger.info("Connectivity check passed.")
      return 0

    # Create backup if requested
    if args.backup and not args.dry_run:
      if args.operation == 'push':
        backup_manager.create_remote_backup()
      else:
        mappings = file_mapping_provider.get_local_to_remote_mappings()
        backup_manager.create_local_backup(mappings)

    # Setup remote dirs for push
    if args.operation == 'push':
      remote_ops.ensure_remote_directory(config.remote_base_dir)

    # Perform operation
    if args.operation == 'push':
      success = push_operation.execute()
    else:
      success = pull_operation.execute()

    if not args.quiet:
      logger.info("AI Config Sync Completed")
      logger.info("═" * 50)

    return 0 if success else 1

  except KeyboardInterrupt:
    logger.error("\nOperation cancelled by user")
    return 130
  except Exception as e:
    logger.error("Unexpected error: %s", e)
    if args.verbose:
      import traceback
      traceback.print_exc()
    return 1


if __name__ == '__main__':
  sys.exit(main())
