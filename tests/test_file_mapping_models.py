"""Tests for mapping Pydantic models."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from sync_ai_config.models import FileMapping, FileMappingConfig, KeepMode


def mapping_entry(**overrides: object) -> dict[str, object]:
  """Create a valid TOML-shaped mapping dictionary for tests."""
  entry: dict[str, object] = {
    "path": ".agents/skills/",
    "keep_mode": "prefer_linux",
  }
  entry.update(overrides)
  return entry


def validation_error_locations(error: ValidationError) -> set[tuple[object, ...]]:
  """Return Pydantic validation error locations."""
  return {tuple(item["loc"]) for item in error.errors()}


def assert_validation_error_location(
  error: ValidationError,
  expected_location: tuple[object, ...],
) -> None:
  """Assert that a validation error includes the expected location."""
  assert expected_location in validation_error_locations(error)


def test_file_mapping_config_accepts_toml_aliases() -> None:
  """TOML-facing aliases should parse into runtime mapping fields."""
  config = FileMappingConfig.model_validate(
    {
      "mappings": [
        mapping_entry(
          path=".tools/config.toml",
          windows_path="AppData/Roaming/Tool/config.toml",
          remote_path=".tools/remote-config.toml",
          keep_mode="keep_both",
          is_directory=True,
          description="Tool config",
        )
      ]
    }
  )

  mapping = config.mappings[0]

  assert mapping.relative_path == Path(".tools/config.toml")
  assert mapping.windows_relative_path == Path("AppData/Roaming/Tool/config.toml")
  assert mapping.remote_relative_path == Path(".tools/remote-config.toml")
  assert mapping.keep_mode == KeepMode.KEEP_BOTH
  assert mapping.is_directory is True
  assert mapping.description == "Tool config"


def test_file_mapping_accepts_internal_field_names() -> None:
  """Internal field names should still work for runtime helpers."""
  mapping = FileMapping.model_validate(
    {
      "relative_path": Path(".codex/config.toml"),
      "windows_relative_path": Path(".codex/config.toml"),
      "remote_relative_path": Path(".codex/config.remote.toml"),
      "keep_mode": KeepMode.PREFER_WINDOWS,
      "is_directory": False,
      "description": "Codex config",
    }
  )

  assert mapping.relative_path == Path(".codex/config.toml")
  assert mapping.windows_relative_path == Path(".codex/config.toml")
  assert mapping.remote_relative_path == Path(".codex/config.remote.toml")
  assert mapping.keep_mode == KeepMode.PREFER_WINDOWS


def test_file_mapping_defaults_optional_fields() -> None:
  """Optional mapping fields should default like the old dataclass did."""
  mapping = FileMappingConfig.model_validate(
    {"mappings": [mapping_entry(path=".claude.json", keep_mode="keep_both")]}
  ).mappings[0]

  assert mapping.relative_path == Path(".claude.json")
  assert mapping.windows_relative_path is None
  assert mapping.remote_relative_path is None
  assert mapping.keep_mode == KeepMode.KEEP_BOTH
  assert mapping.is_directory is False
  assert mapping.description == ""


def test_top_level_version_field_is_rejected() -> None:
  """The mapping config file should not accept a schema version yet."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate({"version": 1, "mappings": []})

  assert_validation_error_location(exc_info.value, ("version",))


def test_missing_top_level_mappings_is_rejected() -> None:
  """The mapping config file must contain a mappings list."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate({})

  assert_validation_error_location(exc_info.value, ("mappings",))


def test_top_level_mappings_must_be_a_list() -> None:
  """The mappings field must be a list of mapping entries."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate({"mappings": mapping_entry()})

  assert_validation_error_location(exc_info.value, ("mappings",))


def test_unknown_mapping_fields_are_rejected() -> None:
  """Unknown mapping fields should fail fast to catch typos."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate(
      {"mappings": [mapping_entry(windowsPath=".codex/config.toml")]}
    )

  assert_validation_error_location(exc_info.value, ("mappings", 0, "windowsPath"))


def test_invalid_keep_mode_is_rejected() -> None:
  """Keep mode values must be one of the declared enum values."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate(
      {"mappings": [mapping_entry(keep_mode="prefer_macos")]}
    )

  assert_validation_error_location(exc_info.value, ("mappings", 0, "keep_mode"))


def test_is_directory_requires_boolean() -> None:
  """Directory flags should be booleans, not string-like values."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate({"mappings": [mapping_entry(is_directory="true")]})

  assert_validation_error_location(exc_info.value, ("mappings", 0, "is_directory"))


@pytest.mark.parametrize("field_name", ["path", "windows_path", "remote_path"])
@pytest.mark.parametrize("path_value", ["", "   "])
def test_empty_path_values_are_rejected(
  field_name: str,
  path_value: str,
) -> None:
  """Path values should not be empty or whitespace-only strings."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate(
      {"mappings": [mapping_entry(**{field_name: path_value})]}
    )

  assert_validation_error_location(exc_info.value, ("mappings", 0, field_name))


@pytest.mark.parametrize("field_name", ["path", "windows_path", "remote_path"])
@pytest.mark.parametrize(
  "path_value",
  [
    "/opt/config.json",
    "C:/Users/me/config.json",
    r"C:\Users\me\config.json",
    "C:Users/me/config.json",
    r"\Users\me\config.json",
  ],
)
def test_absolute_or_drive_qualified_paths_are_rejected(
  field_name: str,
  path_value: str,
) -> None:
  """Path values should be relative fragments, not absolute paths."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate(
      {"mappings": [mapping_entry(**{field_name: path_value})]}
    )

  assert_validation_error_location(exc_info.value, ("mappings", 0, field_name))


@pytest.mark.parametrize("field_name", ["path", "windows_path", "remote_path"])
@pytest.mark.parametrize(
  "path_value",
  [
    "../config.json",
    ".config/../secrets.json",
    r"..\config.json",
    r".config\..\secrets.json",
  ],
)
def test_parent_directory_path_fragments_are_rejected(
  field_name: str,
  path_value: str,
) -> None:
  """Path values should not escape their configured base directory."""
  with pytest.raises(ValidationError) as exc_info:
    FileMappingConfig.model_validate(
      {"mappings": [mapping_entry(**{field_name: path_value})]}
    )

  assert_validation_error_location(exc_info.value, ("mappings", 0, field_name))


def test_trailing_slash_does_not_imply_directory_mapping() -> None:
  """Directory behavior should come from is_directory, not path syntax."""
  mapping = FileMappingConfig.model_validate(
    {"mappings": [mapping_entry(path=".agents/skills/", keep_mode="prefer_linux")]}
  ).mappings[0]

  assert mapping.relative_path == Path(".agents/skills")
  assert mapping.is_directory is False
