"""Tests for the CLI entrypoint setup."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

import sync_ai_config.main as main_module
from sync_ai_config.mapping_config import SYNC_LISTING_CONFIG_ENV
from sync_ai_config.models import RsyncTask


def write_mapping_config(path: Path, mapping_path: str) -> Path:
  """Write a minimal custom mapping config for main integration tests."""
  path.write_text(
    f"""
[[mappings]]
path = "{mapping_path}"
keep_mode = "prefer_linux"
description = "Custom mapping"
""".lstrip(),
    encoding="utf-8",
  )
  return path


def configure_main_success(
  monkeypatch: pytest.MonkeyPatch,
  argv: list[str],
) -> list[RsyncTask]:
  """Configure main() to build tasks without requiring a real rsync command."""
  captured_tasks: list[RsyncTask] = []

  def fake_install(*args: object, **kwargs: object) -> None:
    pass

  def fake_which(command: str) -> str:
    return f"/usr/bin/{command}"

  def fake_execute_tasks(self: object, tasks: list[RsyncTask]) -> bool:
    captured_tasks.extend(tasks)
    return True

  monkeypatch.setattr(main_module, "install_rich_tracebacks", fake_install)
  monkeypatch.setattr(main_module.shutil, "which", fake_which)
  monkeypatch.setattr(main_module.sys, "argv", ["sync-ai-config", *argv])
  monkeypatch.setattr(main_module.TaskExecutor, "execute_tasks", fake_execute_tasks)
  monkeypatch.setenv("SYNC_USER", "sync-user")
  monkeypatch.setenv("SYNC_HOST", "example.com")
  monkeypatch.delenv("SYNC_DIR", raising=False)
  monkeypatch.delenv("WIN_USER", raising=False)

  return captured_tasks


def render_tasks(tasks: list[RsyncTask]) -> str:
  """Render task paths as plain text for config source assertions."""
  return "\n".join(f"{task.src}|{task.dest}" for task in tasks)


def test_main_installs_rich_tracebacks_before_parsing(monkeypatch) -> None:
  """The CLI should enable Rich tracebacks before argument parsing starts."""
  calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

  def fake_install(*args: object, **kwargs: object) -> None:
    calls.append((args, kwargs))

  class SentinelError(RuntimeError):
    """Abort the test after tracebacks are configured."""

  def fake_create_argument_parser() -> object:
    return object()

  def fake_parse_cli_args(parser: object) -> None:
    raise SentinelError

  monkeypatch.setattr(main_module, "install_rich_tracebacks", fake_install)
  monkeypatch.setattr(
    main_module, "create_argument_parser", fake_create_argument_parser
  )
  monkeypatch.setattr(main_module, "parse_cli_args", fake_parse_cli_args)

  with pytest.raises(SentinelError):
    main_module.main()

  assert calls == [((), {"show_locals": False})]


def test_main_requires_operation_before_other_preflight_checks(
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  """A missing operation should fail before rsync or environment checks."""

  def fake_install(*args: object, **kwargs: object) -> None:
    pass

  def fail_which(command: str) -> str | None:
    raise AssertionError("rsync lookup should not run before operation validation")

  monkeypatch.setattr(main_module, "install_rich_tracebacks", fake_install)
  monkeypatch.setattr(main_module.shutil, "which", fail_which)
  monkeypatch.setattr(main_module.sys, "argv", ["sync-ai-config"])
  monkeypatch.delenv("SYNC_USER", raising=False)
  monkeypatch.delenv("SYNC_HOST", raising=False)

  with pytest.raises(SystemExit) as exc_info:
    main_module.main()

  assert exc_info.value.code == 2
  assert "Operation (push/pull) is required" in capsys.readouterr().err


def test_main_uses_packaged_default_without_custom_config(
  monkeypatch: pytest.MonkeyPatch,
  caplog: pytest.LogCaptureFixture,
) -> None:
  """Existing commands should keep using packaged mappings without config input."""
  monkeypatch.delenv(SYNC_LISTING_CONFIG_ENV, raising=False)
  captured_tasks = configure_main_success(monkeypatch, ["push"])
  caplog.set_level(logging.INFO)

  assert main_module.main() == 0

  rendered = render_tasks(captured_tasks)
  assert ".agents/skills" in rendered
  assert ".custom/env-config.json" not in rendered
  assert "Using packaged default mapping config" in caplog.text


def test_main_uses_sync_listing_config_env_before_packaged_default(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  caplog: pytest.LogCaptureFixture,
) -> None:
  """SYNC_LISTING_CONFIG should replace packaged defaults when --config is absent."""
  env_config_path = write_mapping_config(
    tmp_path / "env.toml",
    ".custom/env-config.json",
  )
  monkeypatch.setenv(SYNC_LISTING_CONFIG_ENV, str(env_config_path))
  captured_tasks = configure_main_success(monkeypatch, ["push"])
  caplog.set_level(logging.INFO)

  assert main_module.main() == 0

  rendered = render_tasks(captured_tasks)
  assert ".custom/env-config.json" in rendered
  assert ".agents/skills" not in rendered
  assert f"Using custom mapping config file: {env_config_path}" in caplog.text


def test_main_config_option_overrides_sync_listing_config_env(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """CLI --config should override SYNC_LISTING_CONFIG during task generation."""
  cli_config_path = write_mapping_config(
    tmp_path / "cli.toml",
    ".custom/cli-config.json",
  )
  env_config_path = write_mapping_config(
    tmp_path / "env.toml",
    ".custom/env-config.json",
  )
  monkeypatch.setenv(SYNC_LISTING_CONFIG_ENV, str(env_config_path))
  captured_tasks = configure_main_success(
    monkeypatch,
    ["--config", str(cli_config_path), "push"],
  )

  assert main_module.main() == 0

  rendered = render_tasks(captured_tasks)
  assert ".custom/cli-config.json" in rendered
  assert ".custom/env-config.json" not in rendered
  assert ".agents/skills" not in rendered


def test_main_reports_mapping_config_errors(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  """Mapping config load failures should surface as parser errors."""
  missing_config_path = tmp_path / "missing.toml"
  configure_main_success(
    monkeypatch,
    ["--config", str(missing_config_path), "push"],
  )

  with pytest.raises(SystemExit) as exc_info:
    main_module.main()

  assert exc_info.value.code == 2
  assert "Failed to read mapping config file" in capsys.readouterr().err
