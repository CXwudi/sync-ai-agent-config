"""CLI entrypoint for sync-ai-config."""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import shutil
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Literal, Sequence

from sync_ai_config.config import Config
from sync_ai_config.mappings import ALL_FILE_MAPPINGS, DEFAULT_RSYNC_OPTS
from sync_ai_config.models import Operation, RsyncTask
from sync_ai_config.task_builder import TaskBuilder
from sync_ai_config.task_executor import TaskExecutor


LOG_FORMAT = (
  "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
logging.basicConfig(
  format=LOG_FORMAT,
  handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LOG_LEVELS: tuple[LogLevel, ...] = ("DEBUG", "INFO", "WARNING", "ERROR")


@dataclass
class CliArgs(argparse.Namespace):
  """Typed namespace for parsed CLI arguments."""

  operation: Operation | None = None
  remote_user: str | None = None
  remote_host: str | None = None
  remote_dir: str | None = None
  windows_user: str | None = None
  rsync_opts: str = DEFAULT_RSYNC_OPTS
  log_level: LogLevel = "INFO"
  dry_run: bool = False


def create_argument_parser() -> argparse.ArgumentParser:
  """Create and configure the argument parser."""
  parser = argparse.ArgumentParser(
    description="Sync AI agent configuration files between local machine and remote server"
  )

  parser.add_argument(
    "operation",
    nargs="?",
    type=Operation,
    choices=list(Operation),
    help="Operation to perform",
  )

  remote_group = parser.add_argument_group("remote configuration")
  remote_group.add_argument(
    "-u",
    "--remote-user",
    help="Remote SSH username (overrides SYNC_USER)",
  )
  remote_group.add_argument(
    "-H",
    "--remote-host",
    help="Remote SSH host (overrides SYNC_HOST)",
  )
  remote_group.add_argument(
    "-d",
    "--remote-dir",
    help="Remote directory path (overrides SYNC_DIR)",
  )

  local_group = parser.add_argument_group("local configuration")
  local_group.add_argument(
    "-w",
    "--windows-user",
    help="Windows username (overrides WIN_USER, optional - enables Windows file sync)",
  )

  op_group = parser.add_argument_group("operation options")
  op_group.add_argument(
    "--rsync-opts",
    default=DEFAULT_RSYNC_OPTS,
    help=f'Options to pass to rsync (default: "{DEFAULT_RSYNC_OPTS}")',
  )
  op_group.add_argument(
    "--log-level",
    choices=LOG_LEVELS,
    default="INFO",
    help="Set logging level (default: INFO)",
  )
  op_group.add_argument(
    "--dry-run",
    action="store_true",
    help="Dry run: List all rsync commands without executing",
  )

  info_group = parser.add_argument_group("information options")
  info_group.add_argument(
    "--version", action="version", version=f"%(prog)s {get_version()}"
  )

  return parser


def parse_cli_args(
  parser: argparse.ArgumentParser,
  argv: Sequence[str] | None = None,
) -> CliArgs:
  """Parse command-line arguments into a typed namespace."""
  return parser.parse_args(args=argv, namespace=CliArgs())


def get_version() -> str:
  """Return the package version from metadata or pyproject.toml."""
  try:
    return metadata.version("sync-ai-agent-config")
  except metadata.PackageNotFoundError:
    return _read_version_from_pyproject() or "0.0.0"


def _read_version_from_pyproject() -> str | None:
  """Read the version from pyproject.toml when metadata is unavailable."""
  try:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject_path.exists():
      return None
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    version = project.get("version")
    if isinstance(version, str) and version:
      return version
  except Exception:
    return None
  return None


def config_from_args(args: CliArgs) -> Config:
  """Build a Config from CLI arguments with environment variable fallbacks."""
  remote_user = args.remote_user or os.getenv("SYNC_USER")
  remote_host = args.remote_host or os.getenv("SYNC_HOST")
  remote_base_dir = args.remote_dir or os.getenv(
    "SYNC_DIR", "~/sync-files/ai-agents-related"
  )
  windows_user = args.windows_user or os.getenv("WIN_USER")

  if not remote_user:
    raise ValueError("Remote user must be configured")
  if not remote_host:
    raise ValueError("Remote host must be configured")

  rsync_opts = shlex.split(args.rsync_opts)

  return Config(
    remote_user=remote_user,
    remote_host=remote_host,
    remote_base_dir=Path(remote_base_dir),
    windows_user=windows_user,
    rsync_opts=rsync_opts,
    dry_run=args.dry_run,
  )


def main() -> int:
  """Main entrypoint for the CLI."""
  parser = create_argument_parser()
  args = parse_cli_args(parser)

  numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
  logging.getLogger().setLevel(numeric_level)

  if not shutil.which("rsync"):
    logger.critical(
      "'rsync' command not found. Please install rsync and ensure it is in your PATH."
    )
    return 1

  try:
    config = config_from_args(args)
  except ValueError as exc:
    parser.error(str(exc))

  logger.info("AI Config Sync")
  logger.debug("Configuration: %s", config)

  if not args.operation:
    parser.error("Operation (push/pull) is required")

  task_builder = TaskBuilder(config)
  task_executor = TaskExecutor(config)

  logger.info("Building tasks for %s operation", args.operation.value)
  tasks: list[RsyncTask] = (
    task_builder.build_push_tasks(ALL_FILE_MAPPINGS)
    if args.operation == Operation.PUSH
    else task_builder.build_pull_tasks(ALL_FILE_MAPPINGS)
  )
  logger.debug("Built Tasks: %s", tasks)

  logger.info("Starting %s operation", args.operation.value)
  all_succeeded = task_executor.execute_tasks(tasks)
  if not all_succeeded:
    return 1

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
