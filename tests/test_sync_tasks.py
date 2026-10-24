"""Tests for sync task generation and dry-run execution."""

from __future__ import annotations

import logging
from pathlib import Path

from sync_ai_config.config import Config
from sync_ai_config.mapping_config import load_default_mappings
from sync_ai_config.models import FileMapping, KeepMode, RsyncTask
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


def assert_before(text: str, first: str, second: str) -> None:
  """Assert that the first substring appears before the second substring."""
  assert text.index(first) < text.index(second)


def test_build_push_tasks_matches_supported_agent_files() -> None:
  """Push tasks should include supported agent files in the expected order."""
  tasks = TaskBuilder(build_config()).build_push_tasks(load_default_mappings())
  rendered = render_tasks(tasks)

  assert ".agents/skills" in rendered
  assert ".claude/skills" in rendered
  assert ".gemini/AGENTS.md" in rendered
  assert ".gemini/GEMINI.md" in rendered
  assert ".codex/plugins" in rendered
  assert ".pi/agent/settings.json" in rendered
  assert ".pi/agent/auth.json" in rendered
  assert ".pi/agent/AGENTS.md" in rendered
  assert_before(rendered, ".pi/agent/settings.json", ".config/opencode/opencode.json")
  assert ".gemini/skills" not in rendered
  assert ".codex/skills" not in rendered
  assert ".pi/agent/prompts" not in rendered
  assert ".pi/agent/skills" not in rendered
  assert ".pi/agent/sessions" not in rendered
  assert ".pi/agent/bin" not in rendered


def test_build_pull_tasks_matches_supported_agent_files() -> None:
  """Pull tasks should mirror supported agent files in the expected order."""
  tasks = TaskBuilder(build_config()).build_pull_tasks(load_default_mappings())
  rendered = render_tasks(tasks)

  assert ".agents/skills" in rendered
  assert ".claude/skills" in rendered
  assert ".gemini/AGENTS.md" in rendered
  assert ".gemini/GEMINI.md" in rendered
  assert ".codex/plugins" in rendered
  assert ".pi/agent/settings.json" in rendered
  assert ".pi/agent/auth.json" in rendered
  assert ".pi/agent/AGENTS.md" in rendered
  assert_before(rendered, ".pi/agent/settings.json", ".config/opencode/opencode.json")
  assert ".gemini/skills" not in rendered
  assert ".codex/skills" not in rendered
  assert ".pi/agent/prompts" not in rendered
  assert ".pi/agent/skills" not in rendered
  assert ".pi/agent/sessions" not in rendered
  assert ".pi/agent/bin" not in rendered


def test_dry_run_logs_revised_rsync_commands(caplog) -> None:
  """Dry-run logging should expose the supported agent sync commands."""
  config = build_config(dry_run=True)
  tasks = TaskBuilder(config).build_push_tasks(load_default_mappings())
  executor = TaskExecutor(config)

  caplog.set_level(logging.INFO)

  assert executor.execute_tasks(tasks) is True
  assert ".agents/skills/" in caplog.text
  assert ".claude/skills/" in caplog.text
  assert ".gemini/AGENTS.md" in caplog.text
  assert ".gemini/GEMINI.md" in caplog.text
  assert ".codex/plugins/" in caplog.text
  assert ".pi/agent/settings.json" in caplog.text
  assert ".pi/agent/auth.json" in caplog.text
  assert ".pi/agent/AGENTS.md" in caplog.text
  assert_before(
    caplog.text,
    ".pi/agent/settings.json",
    ".config/opencode/opencode.json",
  )
  assert ".gemini/skills/" not in caplog.text
  assert ".codex/skills/" not in caplog.text
  assert ".pi/agent/prompts/" not in caplog.text
  assert ".pi/agent/skills/" not in caplog.text
  assert ".pi/agent/sessions/" not in caplog.text
  assert ".pi/agent/bin/" not in caplog.text


def test_task_builder_supports_relative_and_absolute_override_paths() -> None:
  """Override paths should resolve relative to base dirs or stay absolute."""
  config = build_config()
  builder = TaskBuilder(config)

  relative_override_mapping = FileMapping(
    relative_path=Path(".tool/config.json"),
    linux_override_path=Path(".config/tool/config.json"),
    windows_override_path=Path("AppData/Roaming/Tool/config.json"),
    remote_relative_path=Path(".remote/tool/config.json"),
    keep_mode=KeepMode.PREFER_LINUX,
    description="Relative override tool",
  )
  absolute_override_mapping = FileMapping(
    relative_path=Path(".tool/system.json"),
    linux_override_path=Path("/etc/tool/system.json"),
    windows_override_path=Path("/mnt/c/ProgramData/Tool/system.json"),
    keep_mode=KeepMode.KEEP_BOTH,
    description="Absolute override tool",
  )

  push_tasks = builder.build_push_tasks(
    [relative_override_mapping, absolute_override_mapping]
  )
  pull_tasks = builder.build_pull_tasks(
    [relative_override_mapping, absolute_override_mapping]
  )

  assert push_tasks[0].src == config.local_home / ".config/tool/config.json"
  assert push_tasks[0].dest == Path(
    "/mnt/c/Users/WindowsUser/AppData/Roaming/Tool/config.json"
  )
  assert (
    push_tasks[1].dest
    == "sync-user@example.com:~/sync-files/ai-agents-related/.remote/tool/config.json"
  )

  assert push_tasks[2].src == Path("/mnt/c/ProgramData/Tool/system.json")
  assert (
    push_tasks[2].dest
    == "sync-user@example.com:~/sync-files/ai-agents-related/.tool/system.windows.json"
  )
  assert push_tasks[3].src == Path("/etc/tool/system.json")
  assert (
    push_tasks[3].dest
    == "sync-user@example.com:~/sync-files/ai-agents-related/.tool/system.linux.json"
  )

  assert pull_tasks[2].dest == Path("/etc/tool/system.json")
  assert pull_tasks[3].dest == Path("/mnt/c/ProgramData/Tool/system.json")
