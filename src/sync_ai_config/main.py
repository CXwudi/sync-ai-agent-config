"""Main entrypoint and logging setup for sync-ai-config."""

from __future__ import annotations

import logging
import shutil
import sys

from rich.traceback import install as install_rich_tracebacks

from sync_ai_config.cli import (
  config_from_args,
  create_argument_parser,
  mapping_config_path_from_args,
  parse_cli_args,
)
from sync_ai_config.mapping_config import MappingConfigError, load_mappings
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


def main() -> int:
  """Main entrypoint for the CLI."""
  install_rich_tracebacks(show_locals=False)

  parser = create_argument_parser()
  args = parse_cli_args(parser)

  numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
  logging.getLogger().setLevel(numeric_level)

  if not args.operation:
    parser.error("Operation (push/pull) is required")

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

  mapping_config_path = mapping_config_path_from_args(args)
  try:
    mappings = load_mappings(mapping_config_path)
  except MappingConfigError as exc:
    parser.error(str(exc))

  if mapping_config_path is None:
    logger.info("Using packaged default mapping config")
  else:
    logger.info("Using custom mapping config file: %s", mapping_config_path)

  task_builder = TaskBuilder(config)
  task_executor = TaskExecutor(config)

  logger.info("Building tasks for %s operation", args.operation.value)
  tasks: list[RsyncTask] = (
    task_builder.build_push_tasks(mappings)
    if args.operation == Operation.PUSH
    else task_builder.build_pull_tasks(mappings)
  )
  logger.debug("Built Tasks: %s", tasks)

  logger.info("Starting %s operation", args.operation.value)
  all_succeeded = task_executor.execute_tasks(tasks)
  if not all_succeeded:
    return 1

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
