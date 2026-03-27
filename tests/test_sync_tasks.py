"""Tests for sync task generation and dry-run execution."""

from __future__ import annotations

import logging
from pathlib import Path

from sync_ai_config.config import Config
from sync_ai_config.mappings import ALL_FILE_MAPPINGS
from sync_ai_config.models import RsyncTask
from sync_ai_config.task_builder import TaskBuilder
from sync_ai_config.task_executor import TaskExecutor


def build_config(*, dry_run: bool = True) -> Config:
  """Create a test configuration with both Linux and Windows targets."""
  return Config(
    remote_user="sync-user",
    remote_host="example.com",
    remote_base_dir=Path("~/sync-files/ai-agents-related"),
    windows_user="WindowsUser",
    rsync_opts=["-avzL"],
    dry_run=dry_run,
  )


def render_tasks(tasks: list[RsyncTask]) -> str:
  """Render tasks as plain text to simplify assertions."""
  return "\n".join(f"{task.description}|{task.src}|{task.dest}" for task in tasks)


def test_build_push_tasks_matches_shared_skills_and_gemini_files() -> None:
  """Push tasks should include the shared agent and Codex plugin paths."""
  tasks = TaskBuilder(build_config()).build_push_tasks(ALL_FILE_MAPPINGS)
  rendered = render_tasks(tasks)

  assert ".agents/skills" in rendered
  assert ".claude/skills" in rendered
  assert ".gemini/AGENTS.md" in rendered
  assert ".gemini/GEMINI.md" in rendered
  assert ".codex/plugins" in rendered
  assert ".gemini/skills" not in rendered
  assert ".codex/skills" not in rendered


def test_build_pull_tasks_matches_shared_skills_and_gemini_files() -> None:
  """Pull tasks should mirror the shared agent and Codex plugin paths."""
  tasks = TaskBuilder(build_config()).build_pull_tasks(ALL_FILE_MAPPINGS)
  rendered = render_tasks(tasks)

  assert ".agents/skills" in rendered
  assert ".claude/skills" in rendered
  assert ".gemini/AGENTS.md" in rendered
  assert ".gemini/GEMINI.md" in rendered
  assert ".codex/plugins" in rendered
  assert ".gemini/skills" not in rendered
  assert ".codex/skills" not in rendered


def test_dry_run_logs_revised_rsync_commands(caplog) -> None:
  """Dry-run logging should expose the shared agent and Codex plugin commands."""
  config = build_config(dry_run=True)
  tasks = TaskBuilder(config).build_push_tasks(ALL_FILE_MAPPINGS)
  executor = TaskExecutor(config)

  caplog.set_level(logging.INFO)

  assert executor.execute_tasks(tasks) is True
  assert ".agents/skills/" in caplog.text
  assert ".claude/skills/" in caplog.text
  assert ".gemini/AGENTS.md" in caplog.text
  assert ".gemini/GEMINI.md" in caplog.text
  assert ".codex/plugins/" in caplog.text
  assert ".gemini/skills/" not in caplog.text
  assert ".codex/skills/" not in caplog.text
