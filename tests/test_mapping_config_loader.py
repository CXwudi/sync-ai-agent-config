"""Tests for mapping config loading and error handling."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from sync_ai_config.mapping_config import (
  MappingConfigError,
  load_default_mappings,
  load_mappings,
  load_mappings_from_path,
  read_default_mappings_text,
)
from sync_ai_config.models import FileMappingConfig, KeepMode


CUSTOM_CONFIG = """
[[mappings]]
path = ".custom/config.json"
keep_mode = "prefer_linux"
description = "Custom config"
""".lstrip()


def write_config(path: Path, text: str = CUSTOM_CONFIG) -> Path:
  """Write a UTF-8 mapping config file for tests."""
  path.write_text(text, encoding="utf-8")
  return path


def test_read_default_mappings_text_reads_packaged_resource() -> None:
  """The packaged default should be readable as a package resource."""
  text = read_default_mappings_text()

  assert "[[mappings]]" in text
  assert 'path = ".agents/skills/"' in text


def test_load_default_mappings_matches_manual_parse() -> None:
  """Default loader should return the validated packaged TOML mappings."""
  data = tomllib.loads(read_default_mappings_text())
  expected_mappings = FileMappingConfig.model_validate(data).mappings

  assert [mapping.model_dump() for mapping in load_default_mappings()] == [
    mapping.model_dump() for mapping in expected_mappings
  ]


def test_load_mappings_none_uses_packaged_default() -> None:
  """The generic loader should use defaults when no custom path is supplied."""
  assert [mapping.model_dump() for mapping in load_mappings(None)] == [
    mapping.model_dump() for mapping in load_default_mappings()
  ]


def test_load_mappings_custom_path_replaces_defaults(tmp_path: Path) -> None:
  """A custom config should replace the packaged defaults entirely."""
  custom_path = write_config(tmp_path / "mappings.toml")

  mappings = load_mappings(custom_path)

  assert len(mappings) == 1
  assert mappings[0].relative_path == Path(".custom/config.json")
  assert mappings[0].keep_mode == KeepMode.PREFER_LINUX
  assert ".agents/skills" not in {
    mapping.relative_path.as_posix() for mapping in mappings
  }


def test_load_mappings_from_path_reads_utf8(tmp_path: Path) -> None:
  """Custom mapping config files should be read with UTF-8 encoding."""
  custom_path = write_config(
    tmp_path / "utf8-mappings.toml",
    """
[[mappings]]
path = ".custom/unicode.json"
keep_mode = "prefer_linux"
description = "Unicode café config"
""".lstrip(),
  )

  mappings = load_mappings_from_path(custom_path)

  assert mappings[0].description == "Unicode café config"


def test_load_mappings_expands_custom_path_user_home(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """Custom paths should support user-home expansion."""
  home_dir = tmp_path / "home"
  home_dir.mkdir()
  custom_path = write_config(home_dir / "mappings.toml")
  monkeypatch.setenv("HOME", str(home_dir))
  monkeypatch.setenv("USERPROFILE", str(home_dir))

  mappings = load_mappings(Path("~/mappings.toml"))

  assert mappings[0].relative_path == Path(".custom/config.json")
  assert custom_path.exists()


def test_missing_custom_config_raises_error(tmp_path: Path) -> None:
  """A missing custom config should fail instead of falling back to defaults."""
  missing_path = tmp_path / "missing.toml"

  with pytest.raises(MappingConfigError) as exc_info:
    load_mappings(missing_path)

  message = str(exc_info.value)
  assert str(missing_path) in message
  assert "Failed to read mapping config file" in message


def test_invalid_toml_raises_error(tmp_path: Path) -> None:
  """Invalid custom TOML should fail with file and parse context."""
  config_path = write_config(tmp_path / "invalid.toml", "[[mappings]\npath =")

  with pytest.raises(MappingConfigError) as exc_info:
    load_mappings(config_path)

  message = str(exc_info.value)
  assert str(config_path) in message
  assert "Invalid TOML" in message


def test_schema_invalid_toml_preserves_validation_location(tmp_path: Path) -> None:
  """Schema errors should preserve useful dotted validation locations."""
  config_path = write_config(
    tmp_path / "schema-invalid.toml",
    """
[[mappings]]
keep_mode = "prefer_linux"
""".lstrip(),
  )

  with pytest.raises(MappingConfigError) as exc_info:
    load_mappings(config_path)

  message = str(exc_info.value)
  assert str(config_path) in message
  assert "mappings.0.path" in message


@pytest.mark.parametrize(
  ("toml_text", "expected_location"),
  [
    (
      """
[[mappings]]
path = ".custom/config.json"
keep_mode = "prefer_linux"
windowsPath = ".custom/windows.json"
""".lstrip(),
      "mappings.0.windowsPath",
    ),
    (
      """
[[mappings]]
path = ".custom/config.json"
keep_mode = "prefer_macos"
""".lstrip(),
      "mappings.0.keep_mode",
    ),
    (
      """
[[mappings]]
path = ""
keep_mode = "prefer_linux"
""".lstrip(),
      "mappings.0.path",
    ),
    (
      """
[[mappings]]
path = "/tmp/config.json"
keep_mode = "prefer_linux"
""".lstrip(),
      "mappings.0.path",
    ),
  ],
)
def test_loader_wraps_schema_validation_errors(
  tmp_path: Path,
  toml_text: str,
  expected_location: str,
) -> None:
  """Loader errors should wrap validation failures without hiding locations."""
  config_path = write_config(tmp_path / "invalid-schema.toml", toml_text)

  with pytest.raises(MappingConfigError) as exc_info:
    load_mappings(config_path)

  message = str(exc_info.value)
  assert str(config_path) in message
  assert expected_location in message


def test_unreadable_custom_config_raises_error(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """Read failures should be wrapped as mapping config errors."""
  config_path = write_config(tmp_path / "unreadable.toml")

  def fail_read_text(self: Path, *, encoding: str | None = None) -> str:
    raise PermissionError("permission denied for test")

  monkeypatch.setattr(Path, "read_text", fail_read_text)

  with pytest.raises(MappingConfigError) as exc_info:
    load_mappings_from_path(config_path)

  assert "permission denied for test" in str(exc_info.value)


def test_loader_does_not_require_declared_paths_to_exist(tmp_path: Path) -> None:
  """Declarative mapping paths should not need to exist on the local machine."""
  config_path = write_config(
    tmp_path / "nonexistent-paths.toml",
    """
[[mappings]]
path = ".definitely/not/a/real/file.json"
windows_path = "Definitely/Not/Real/file.json"
remote_path = ".remote/not-real/file.json"
keep_mode = "prefer_linux"
""".lstrip(),
  )

  mappings = load_mappings(config_path)

  assert mappings[0].relative_path == Path(".definitely/not/a/real/file.json")
  assert mappings[0].windows_relative_path == Path("Definitely/Not/Real/file.json")
  assert mappings[0].remote_relative_path == Path(".remote/not-real/file.json")
