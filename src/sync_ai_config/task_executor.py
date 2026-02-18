"""Execute rsync tasks."""

from __future__ import annotations

import logging
import subprocess
from typing import List

from sync_ai_config.config import Config
from sync_ai_config.models import RsyncTask


logger = logging.getLogger(__name__)


class TaskExecutor:
  """Executes rsync tasks."""

  def __init__(self, config: Config):
    self.config = config

  def execute_tasks(self, tasks: List[RsyncTask]) -> None:
    """Execute all tasks."""
    logger.info("Executing %d tasks", len(tasks))
    for task in tasks:
      self._execute_one_task(task)
    if self.config.dry_run:
      logger.info("Dry run complete")

  def _execute_one_task(self, task: RsyncTask) -> bool:
    """Execute a single rsync task."""
    src = str(task.src)
    dest = str(task.dest)

    if task.is_directory:
      if not src.endswith('/'):
        src += '/'
      if not dest.endswith('/'):
        dest += '/'

    cmd = ['rsync', *self.config.rsync_opts, src, dest]
    logger.info("Executing for %s:\n%s", task.description, ' '.join(cmd))

    if self.config.dry_run:
      return True

    try:
      result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
      )
      if result.returncode == 0:
        logger.info("Success: %s", task.description)
        return True
      logger.error("Failed: %s - Return code: %d", task.description, result.returncode)
      if result.stderr:
        logger.error("Error output: %s", result.stderr.strip())
      return False
    except subprocess.TimeoutExpired:
      logger.error("Timeout: %s", task.description)
      return False
    except Exception as exc:
      logger.error("Exception executing %s: %s", task.description, exc)
      return False
