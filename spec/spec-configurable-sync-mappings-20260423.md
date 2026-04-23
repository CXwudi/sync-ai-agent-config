# Configurable Sync Mappings Design Spec

## Problem or Goal

GitHub issue [#10](https://github.com/CXwudi/sync-ai-agent-config/issues/10)
asks the project to stop hardcoding the sync file and folder list in Python and
make that list configurable via a file. The goal is to preserve the current sync
behavior by default while allowing users to replace the mapping list with a
custom config file.

## Context

The current implementation has a clean execution pipeline: the CLI resolves
runtime settings, `TaskBuilder` turns a list of `FileMapping` objects into
`RsyncTask` objects, and `TaskExecutor` executes those tasks. The hardcoded part
is isolated in `src/sync_ai_config/mappings.py`, where grouped Python lists are
combined into `ALL_FILE_MAPPINGS`.

The implementation should keep the existing task-building behavior and move the
mapping data out of Python code. The current list should become the packaged
default config file. A user-provided config file should replace that default
mapping list entirely, not merge with or extend it.

The project currently has no runtime dependencies, but the user confirmed that
adding a dependency is acceptable. Because the project uses `uv`, adding
Pydantic is acceptable if it improves validation and keeps the implementation
clear.

## Design Options

### Option 1: TOML plus manual dataclass parsing

Keep `FileMapping` as a dataclass and add a TOML loader that manually validates
dictionaries before constructing `FileMapping` objects.

This option avoids runtime dependencies and keeps models lightweight. It also
uses `tomllib`, which is already available in Python 3.11+. However, it requires
custom validation logic for required fields, unknown fields, enum values,
optional paths, boolean values, empty strings, and error messages. As the schema
grows, the manual parser would become another source of maintenance risk.

### Option 2: TOML plus Pydantic config models

Use TOML for the file format and Pydantic v2 for validation. Convert the current
`FileMapping` dataclass into a Pydantic model, and add a thin top-level
`FileMappingConfig` model containing `mappings: list[FileMapping]`.

This option introduces a runtime dependency, but it keeps validation centralized
and makes the config boundary explicit. It also avoids duplicating the mapping
schema because the same `FileMapping` object can be used after parsing by the
existing `TaskBuilder` code.

### Option 3: Separate external config model and runtime dataclass

Add a Pydantic model for config-file entries, keep `FileMapping` as a dataclass,
and convert parsed config entries into runtime `FileMapping` objects.

This option creates a clean separation between external config syntax and
internal runtime objects. It would be useful if the external config were
expected to diverge significantly from the runtime model. For this issue, the
two shapes are almost identical, so this adds duplicate fields and conversion
code without a clear near-term benefit.

## Recommendation

Use **Option 2: TOML plus Pydantic config models**.

The recommended design is:

1. Store the current hardcoded mapping list as a packaged TOML file, for example
   `src/sync_ai_config/default_mappings.toml`.
2. Load that packaged TOML file through `importlib.resources` when no custom
   config path is provided.
3. Add the custom config path input as exactly `--config PATH`, with
   `SYNC_LISTING_CONFIG` as the environment fallback.
4. When a custom config file is provided, use it as the complete mapping list.
   Do not merge it with the packaged default.
5. Drop any top-level config `version` field for now. The file shape should stay
   minimal until schema versioning is actually needed.
6. Convert `FileMapping` from a dataclass into a Pydantic v2 `BaseModel`.
7. Add a top-level `FileMappingConfig` Pydantic model containing only the
   mapping collection and any direct file-shape validation needed.
8. Keep the existing runtime `Config` dataclass unchanged because it represents
   resolved CLI/environment runtime settings, not the declarative mapping list.
9. Keep `TaskBuilder` behavior unchanged except for type hint modernization if
   useful.
10. Keep `DEFAULT_RSYNC_OPTS` in Python for this issue because issue #10 is
    specifically about the files/folders list, not every runtime setting.

### Default config packaging and loading

The default mapping file should be loaded with standard package-resource APIs:

```python
from importlib import resources

DEFAULT_MAPPINGS_RESOURCE = "default_mappings.toml"

def read_default_mappings_text() -> str:
  """Read the packaged default mapping config."""
  return resources.files("sync_ai_config").joinpath(
    DEFAULT_MAPPINGS_RESOURCE
  ).read_text(encoding="utf-8")
```

The implementation should not rely on a source-tree-relative path for the
default config. That keeps editable installs, installed wheels, and bundled
executables aligned around the same runtime lookup behavior.

Packaging changes should make the TOML resource available at
`sync_ai_config/default_mappings.toml`:

- Wheel/editable package: explicitly include
  `src/sync_ai_config/default_mappings.toml` as package data. If Hatchling does
  not already include it through the existing `packages` setting, add an
  explicit wheel include/force-include entry in `pyproject.toml`.
- PyInstaller one-file executable: include the data file under the
  `sync_ai_config` package destination, for example by changing the `justfile`
  build command to pass
  `--add-data src/sync_ai_config/default_mappings.toml:sync_ai_config`.
- Existing `sync-ai-config.spec`: if it remains part of the build workflow, add
  the same TOML file to `datas`, for example
  `datas=[("src/sync_ai_config/default_mappings.toml", "sync_ai_config")]`.

### Proposed TOML shape

The default and custom config files should use user-facing field names:

```toml
[[mappings]]
path = ".agents/skills/"
keep_mode = "prefer_linux"
is_directory = true
description = "Shared agent skills"

[[mappings]]
path = ".claude.json"
keep_mode = "keep_both"
description = "Claude Code config"

[[mappings]]
path = ".vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
windows_path = "AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
keep_mode = "prefer_linux"
description = "Cline MCP settings for VSCode"
```

There should be no top-level `version` field. The file should contain:

```toml
[[mappings]]
# mapping fields...
```

### Proposed model shape

The existing runtime model can become the parsed config model:

```python
class FileMapping(BaseModel):
  """Windows, Linux, Remote, 3-way file mapping."""

  model_config = ConfigDict(populate_by_name=True, extra="forbid")

  relative_path: Path = Field(alias="path")
  windows_relative_path: Path | None = Field(default=None, alias="windows_path")
  remote_relative_path: Path | None = Field(default=None, alias="remote_path")
  keep_mode: KeepMode
  is_directory: bool = False
  description: str = ""
```

The top-level config model should be intentionally small:

```python
class FileMappingConfig(BaseModel):
  """Config file containing sync file and directory mappings."""

  model_config = ConfigDict(extra="forbid")

  mappings: list[FileMapping]
```

`FileMappingConfig` contains the list of `FileMapping` objects. It should not
contain a `version` field.

### Config path precedence

The config path contract is:

1. CLI `--config PATH`
2. Environment variable `SYNC_LISTING_CONFIG`
3. Packaged default config file

- `--config` has no short alias in the first implementation.
- Custom config paths from either source are resolved by applying
  `Path(value).expanduser()` and then using normal
  process-current-working-directory semantics for relative paths.
- If `--config` or `SYNC_LISTING_CONFIG` points to a missing file, unreadable
  file, invalid TOML file, or schema-invalid file, the CLI must fail with a
  clear error and must not fall back to the packaged default.
- The packaged default is used only when neither `--config` nor
  `SYNC_LISTING_CONFIG` is set.

### Validation behavior

The config loader should validate at least:

- `mappings` is present and is a list.
- Each mapping has a non-empty `path`.
- `keep_mode` is one of the existing `KeepMode` enum values:
  - `prefer_windows`
  - `prefer_linux`
  - `keep_both`
- `is_directory`, when present, is a boolean.
- Unknown fields are rejected to catch typos.
- `windows_path` and `remote_path`, when present, are non-empty paths.
- `path`, `windows_path`, and `remote_path` are relative path fragments, not
  absolute paths. `path` is relative to the Linux home directory, `windows_path`
  is relative to the Windows user directory, and `remote_path` is relative to
  the configured remote base directory.
- The mapping paths are declarative and are not required to exist on the local
  machine during parsing.

The implementation should wrap TOML parse errors and Pydantic validation errors
into user-friendly CLI errors. Detailed validation paths are useful; they should
not be hidden.

## Scope and Non-Goals

- In scope:
  - Move the current hardcoded mapping list into a packaged TOML default config.
  - Add Pydantic validation for mapping config files.
  - Add `FileMappingConfig` containing `mappings: list[FileMapping]`.
  - Load the packaged default config automatically.
  - Add custom config support that replaces the default mappings entirely.
  - Preserve existing push/pull task behavior for the current mapping list.
  - Update tests and user-facing documentation for the new config behavior.

- Out of scope:
  - Trimming, removing, or redesigning the current default mapping list.
  - Supporting merge, extend, or override semantics between custom and default
    mappings.
  - Adding include/import support for config files.
  - Adding schema versioning.
  - Moving remote host, remote dir, Windows user, dry-run, or rsync options into
    the mapping config file.
  - Changing `TaskBuilder` synchronization semantics.

## Risks and Open Questions

- Packaging the default TOML must be verified for editable installs, wheel
  builds, and the single-file executable path if PyInstaller is still used. The
  chosen runtime mechanism is `importlib.resources`; package metadata and
  PyInstaller data-file options must include the TOML resource so that mechanism
  succeeds outside the source tree.
- Pydantic `Path` parsing should be checked carefully because these paths are
  intentionally relative to Linux home, Windows user home, or the remote base
  directory. Validation should not require paths to exist locally, but should
  reject absolute paths that would bypass those base directories.
- Directory handling still depends on `is_directory = true`; paths ending in `/`
  should not be the only source of truth.
- The current dataclass `FileMapping.__iter__` tuple-unpacking helper appears
  unused. It can be dropped unless tests or downstream code rely on it.
- `DEFAULT_RSYNC_OPTS` currently lives in `mappings.py`, which may no longer be
  an appropriate module after mappings move to TOML. It should either stay in a
  small constants module or move to a more suitable existing module.

## Validation Considerations

Implementation should be validated with unit tests and CLI-oriented tests:

- Loading the packaged default config returns the same number and order of
  mappings as the current `ALL_FILE_MAPPINGS` behavior.
- Push task generation from the packaged default config preserves expected
  supported files and ordering.
- Pull task generation from the packaged default config preserves expected
  supported files and ordering.
- A custom TOML config replaces the default entirely.
- CLI `--config` takes precedence over `SYNC_LISTING_CONFIG`.
- `SYNC_LISTING_CONFIG` takes precedence over the packaged default.
- Missing custom config path fails clearly.
- Invalid TOML fails clearly.
- Unknown mapping fields fail clearly.
- Invalid `keep_mode` fails clearly.
- Directory mappings still render trailing slashes in dry-run rsync commands.
- Existing commands still work without specifying a config path.

After implementation, run:

```sh
just test
just typecheck
just lint
```

Also review whether `README.md` and `common-doc/design-doc-draft.md` need
updates; based on the current docs, they likely do.

## References

<!-- markdownlint-disable MD013 -->

| Resource                                                                     | Description                                                                                               | Other Notes if any |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------ |
| [GitHub issue #10](https://github.com/CXwudi/sync-ai-agent-config/issues/10) | Source ticket requesting configurable sync files/folders instead of hardcoded mappings.                   | Must Read          |
| ![a file](src/sync_ai_config/mappings.py:1:246)                              | Current hardcoded default mapping lists and `ALL_FILE_MAPPINGS`.                                          | Must Read          |
| ![a file](src/sync_ai_config/models.py:18:63)                                | Current `KeepMode`, `FileMapping`, and `RsyncTask` models.                                                | Must Read          |
| ![a file](src/sync_ai_config/cli.py:17:206)                                  | CLI currently imports `ALL_FILE_MAPPINGS`, resolves runtime config, and passes mappings to `TaskBuilder`. | Important          |
| ![a file](src/sync_ai_config/task_builder.py:16:241)                         | Existing mapping-to-rsync-task behavior that should remain mostly unchanged.                              | Important          |
| ![a file](tests/test_sync_tasks.py:1:108)                                    | Existing tests asserting supported mapping behavior and dry-run output.                                   | Important          |
| ![a file](README.md:1:56)                                                    | User-facing usage docs that need config-file option documentation after implementation.                   | Important          |
| ![a file](common-doc/design-doc-draft.md:1:212)                              | Project design notes describing the current hardcoded sync operations.                                    | Important          |
| ![a file](pyproject.toml:1:24)                                               | Project metadata, dependencies, package build settings, and Ruff indentation preference.                  | Important          |
| ![a file](justfile:17:19)                                                    | Current PyInstaller build command that should include the packaged default TOML resource.                 | Important          |
| ![a file](sync-ai-config.spec:1:33)                                          | Existing PyInstaller spec with an empty `datas` list; relevant if this build path remains in use.         | Important          |

<!-- markdownlint-enable MD013 -->
