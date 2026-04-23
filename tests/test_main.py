"""Tests for the CLI entrypoint setup."""

from __future__ import annotations

import pytest

import sync_ai_config.main as main_module


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
