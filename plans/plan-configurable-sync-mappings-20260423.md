# Configurable Sync Mappings Implementation Plan

> **For agentic workers:** Use the harness's preferred task-tracking and
> delegation tools when available. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Replace the hardcoded sync file/folder mapping list with a validated
TOML mapping config while preserving the current packaged defaults.

**Source of Truth:** Approved design spec at
`spec/spec-configurable-sync-mappings-20260423.md` and GitHub issue #10.

**Scope:** Implement TOML + Pydantic mapping config loading, package the current
mapping list as the default config, add `--config PATH`/`SYNC_LISTING_CONFIG`
custom config support, update tests, packaging metadata, and docs. Excludes
trimming the current default mappings, merge/extend semantics, schema
versioning, and moving runtime settings such as remote host or rsync options
into the mapping config.

**Approach:** Work incrementally from the data model outward: add the Pydantic
schema, move default data into a packaged TOML resource, add a small loader,
then wire the CLI to load mappings before task building. Preserve `TaskBuilder`
and `TaskExecutor` behavior except for minimal type-hint adjustments, and use
tests to prove default behavior stays compatible while custom configs replace
the default entirely.

**Verification:** Run targeted unit tests after each slice, then run
`just test`, `just typecheck`, and `just lint`. For packaging, run `uv build`
and inspect the built wheel for `sync_ai_config/default_mappings.toml`; run
`just build-exe` if the environment supports PyInstaller bundling.

---

## Implementation Tasks

### Task 1: Establish baseline and dependency setup

#### 1.1 Intent

Start from a known-good repository state, add the approved runtime dependency,
and avoid mixing dependency lockfile changes with later behavior changes.

#### 1.2 Files

- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Read: `AGENTS.md`
- Read: `common-doc/README.md`
- Read: `common-doc/design-doc-draft.md`

#### 1.3 Dependencies

None.

- [ ] **Step 1:** Confirm working tree state with `git status --short` and note
      any pre-existing user changes before editing.
- [ ] **Step 2:** Run the current test suite with `just test` to capture the
      baseline behavior before refactoring.
- [ ] **Step 3:** Add Pydantic v2 with `uv add pydantic`, producing the
      dependency and lockfile changes.
- [ ] **Step 4:** Run
      `uv run python -c "import pydantic; print(pydantic.__version__)"` to
      confirm the dependency resolves in the project environment.

#### 1.4 Verification

- Run: `just test`
- Run: `uv run python -c "import pydantic; print(pydantic.__version__)"`
- Expect: Existing tests pass before behavior changes, and Pydantic imports from
  the uv-managed environment.

#### 1.5 Notes

- Use `uv run ...` rather than bare `python`, per project guidance.
- If adding the dependency needs network access and fails for a sandbox/network
  reason, rerun the same dependency command with escalation approval.

### Task 2: Convert mapping models to validated Pydantic models

#### 2.1 Intent

Make `FileMapping` usable as both the parsed config model and the runtime object
consumed by `TaskBuilder`, and add the thin top-level `FileMappingConfig` model
specified by the design.

#### 2.2 Files

- Modify: `src/sync_ai_config/models.py`
- Test: `tests/test_file_mapping_models.py`

#### 2.3 Dependencies

Task 1.

- [ ] **Step 1:** Keep `Operation`, `KeepMode`, and `RsyncTask` in `models.py`;
      convert only `FileMapping` from `@dataclass` to a Pydantic v2 `BaseModel`.
- [ ] **Step 2:** Add aliases exactly as specified:
  - `relative_path: Path = Field(alias="path")`
  - `windows_relative_path: Path | None = Field(default=None, alias="windows_path")`
  - `remote_relative_path: Path | None = Field(default=None, alias="remote_path")`
- [ ] **Step 3:** Configure `FileMapping` with
      `ConfigDict(populate_by_name=True, extra="forbid")` so internal field
      names still work in tests/helpers while custom config files reject typos.
- [ ] **Step 4:** Add `FileMappingConfig(BaseModel)` with
      `mappings: list[FileMapping]`, `extra="forbid"`, and no `version` field.
- [ ] **Step 5:** Add Pydantic validators for path fields that reject empty or
      whitespace-only values before `Path` coercion turns them into `.`.
- [ ] **Step 6:** Add validators that reject absolute path fragments. Use both
      POSIX and Windows-aware checks, such as `Path(value).is_absolute()` plus
      `PureWindowsPath(value).is_absolute()`/drive detection, so inputs like
      `/tmp/file`, `C:/Users/me/file`, or `C:\\Users\\me\\file` cannot bypass
      the configured base directories.
- [ ] **Step 7:** Preserve the existing `FileMapping.__iter__` helper unless an
      explicit search proves no tests or downstream code depend on
      tuple-unpacking; keeping it minimizes this refactor's behavioral surface.
- [ ] **Step 8:** Add focused model tests for valid aliases, internal-name
      population, missing `mappings`, unknown fields, invalid `keep_mode`, empty
      paths, and absolute paths.

#### 2.4 Verification

- Run: `uv run pytest tests/test_file_mapping_models.py -v`
- Run: `uv run ty check src/sync_ai_config tests`
- Expect: Pydantic parses valid mapping entries into `FileMapping` objects,
  rejects invalid entries with useful validation paths, and existing runtime
  type consumers still typecheck or have a clear follow-up adjustment.

#### 2.5 Notes

- The paths are declarative fragments and must not be required to exist on disk.
- Directory semantics must continue to depend on `is_directory = true`; a
  trailing slash in the TOML path is not enough.
- Pydantic should parse `KeepMode` from string enum values like
  `"prefer_linux"`.

#### 2.6 Test cases to add

- [ ] `FileMappingConfig` accepts a valid TOML-shaped dictionary with
      user-facing aliases (`path`, `windows_path`, `remote_path`) and returns
      `Path` objects plus the expected `KeepMode` enum.
- [ ] `FileMapping` still accepts internal field names such as `relative_path`
      and `windows_relative_path` to preserve runtime/test helper compatibility.
- [ ] Omitted optional fields default correctly:
      `windows_relative_path is None`, `remote_relative_path is None`,
      `is_directory is False`, and `description == ""`.
- [ ] A top-level `version` field is rejected, proving the config has no schema
      version for this issue.
- [ ] Missing top-level `mappings` is rejected with an error location that makes
      the missing field obvious.
- [ ] Unknown mapping fields are rejected, for example `windowsPath` or
      `relative_path_typo`.
- [ ] Invalid `keep_mode` values are rejected and the message points to the
      offending mapping entry.
- [ ] Empty or whitespace-only values are rejected for `path`, `windows_path`,
      and `remote_path`.
- [ ] Absolute POSIX paths are rejected for all path fields.
- [ ] Absolute Windows paths and drive-qualified paths are rejected for all path
      fields.
- [ ] Directory entries require `is_directory = true`; a trailing slash alone
      does not set `is_directory`.
- [ ] If `FileMapping.__iter__` is preserved, tuple-unpacking returns fields in
      the same order as the previous dataclass helper.

### Task 3: Move the default mapping data into a packaged TOML file

#### 3.1 Intent

Remove the hardcoded Python mapping list while preserving the current default
mapping count, order, paths, keep modes, directory flags, and descriptions.

#### 3.2 Files

- Create: `src/sync_ai_config/default_mappings.toml`
- Modify: `src/sync_ai_config/mappings.py`
- Test: `tests/test_default_mappings.py`
- Test: `tests/test_sync_tasks.py`
- Read: `src/sync_ai_config/mappings.py`

#### 3.3 Dependencies

Task 2.

- [ ] **Step 1:** Translate every active `FileMapping` currently included in
      `ALL_FILE_MAPPINGS` into `[[mappings]]` TOML entries using user-facing
      keys: `path`, optional `windows_path`, optional `remote_path`,
      `keep_mode`, optional `is_directory`, and optional `description`.
- [ ] **Step 2:** Preserve ordering exactly: common agent mappings, Claude Code,
      Gemini CLI, Codex CLI, Pi Coding Agent, OpenCode, and Cline.
- [ ] **Step 3:** Do not add the commented-out Cline Rules mapping to the
      default TOML because it is not part of the active current default list.
- [ ] **Step 4:** Keep `DEFAULT_RSYNC_OPTS` in Python, but move it to a small
      constants-style module if keeping it in `mappings.py` feels misleading
      after the hardcoded mappings are removed. Minimize import churn either
      way.
- [ ] **Step 5:** Remove `ALL_FILE_MAPPINGS` and the grouped Python mapping
      lists from runtime use. If a temporary compatibility helper is kept during
      the refactor, ensure final CLI behavior does not read hardcoded mapping
      lists.
- [ ] **Step 6:** Add tests that load the packaged default and assert key
      compatibility signals: total mapping count is 26, first mapping is
      `.agents/skills`, `.claude.json` remains `keep_both`, directory mappings
      keep `is_directory = true`, and the final active Cline mapping retains its
      `windows_path`.

#### 3.4 Verification

- Run:
  `uv run pytest tests/test_default_mappings.py tests/test_sync_tasks.py -v`
- Expect: Default TOML parses into the same active mapping set that the old
  `ALL_FILE_MAPPINGS` represented.

#### 3.5 Notes

- Avoid relying on a source-tree path in runtime code; source-tree access is
  acceptable only for tests that explicitly inspect repository files.
- Keep descriptions exactly unless there is a clear typo; preserving text makes
  behavior and dry-run logs easier to compare.

#### 3.6 Test cases to add

- [ ] The packaged default TOML parses successfully into `FileMappingConfig`.
- [ ] The default mapping count is exactly 26, matching the current active
      `ALL_FILE_MAPPINGS` list and excluding the commented-out Cline Rules
      mapping.
- [ ] The first mapping remains `.agents/skills/` with
      `keep_mode = "prefer_linux"` and `is_directory = true`.
- [ ] The Claude `.claude.json` mapping remains `keep_both`, preserving the
      `.linux`/`.windows` remote split behavior.
- [ ] The Claude directory mappings for `.claude/agents/` and `.claude/skills/`
      keep `is_directory = true`.
- [ ] The Codex `.codex/plugins/` mapping keeps `is_directory = true`.
- [ ] The Pi Coding Agent mappings still appear before OpenCode mappings to
      preserve current task ordering.
- [ ] OpenCode directory mappings for `prompts`, `agents`, `commands`, and
      `plugins` keep `is_directory = true`.
- [ ] The final active Cline mapping keeps its custom `windows_path` and no
      custom `remote_path`.
- [ ] No default mapping has an absolute `path`, `windows_path`, or
      `remote_path`.
- [ ] `TaskBuilder(build_config()).build_push_tasks(load_default_mappings())`
      still includes the expected supported agent files and excludes the
      currently unsupported paths.
- [ ] `TaskBuilder(build_config()).build_pull_tasks(load_default_mappings())`
      still includes the expected supported agent files and excludes the
      currently unsupported paths.

### Task 4: Add mapping config loader and error boundary

#### 4.1 Intent

Create a focused loader that reads either the packaged default resource or a
custom TOML file, validates it through `FileMappingConfig`, and exposes clear
errors to the CLI.

#### 4.2 Files

- Create: `src/sync_ai_config/mapping_config.py`
- Modify: `src/sync_ai_config/__init__.py` only if exports are needed
- Test: `tests/test_mapping_config_loader.py`

#### 4.3 Dependencies

Tasks 2 and 3.

- [ ] **Step 1:** Add constants such as
      `DEFAULT_MAPPINGS_RESOURCE = "default_mappings.toml"` and
      `SYNC_LISTING_CONFIG_ENV = "SYNC_LISTING_CONFIG"` in the loader or CLI
      layer.
- [ ] **Step 2:** Implement `read_default_mappings_text()` with
      `importlib.resources.files("sync_ai_config").joinpath(DEFAULT_MAPPINGS_RESOURCE).read_text(encoding="utf-8")`.
- [ ] **Step 3:** Implement `load_default_mappings() -> list[FileMapping]` for
      callers/tests that want the packaged default explicitly.
- [ ] **Step 4:** Implement
      `load_mappings_from_path(path: Path) -> list[FileMapping]` that reads a
      custom file after `Path(value).expanduser()` is applied by the caller or
      helper.
- [ ] **Step 5:** Implement a single public helper such as
      `load_mappings(config_path: Path | None = None) -> list[FileMapping]`
      where `None` means packaged default and a path means complete replacement.
- [ ] **Step 6:** Add a documented `MappingConfigError(ValueError)` and wrap
      missing file, unreadable file, invalid TOML, packaged-resource read
      failures, and Pydantic validation failures into this error. Preserve
      validation details in the message instead of hiding field paths.
- [ ] **Step 7:** Ensure custom config failures never fall back to the packaged
      default.
- [ ] **Step 8:** Add tests for custom replacement, missing file, invalid TOML,
      schema-invalid TOML, unknown mapping fields, invalid keep mode, and
      default resource loading.

#### 4.4 Verification

- Run: `uv run pytest tests/test_mapping_config_loader.py -v`
- Expect: Loader behavior matches the spec, especially custom replacement and no
  fallback on custom config errors.

#### 4.5 Notes

- Keep environment-variable precedence out of the loader unless it stays
  trivially testable; a pure loader plus a small CLI resolver is easier to
  reason about.
- Config errors should be raised before any task-building starts.

#### 4.6 Test cases to add

- [ ] `read_default_mappings_text()` reads the packaged resource through
      `importlib.resources`, not a source-tree-relative path.
- [ ] `load_default_mappings()` returns the same validated mapping list as
      parsing `read_default_mappings_text()` manually through
      `FileMappingConfig`.
- [ ] `load_mappings(None)` uses the packaged default.
- [ ] `load_mappings(custom_path)` returns only the entries from the custom TOML
      file, proving custom config replaces defaults entirely.
- [ ] A custom config with a single mapping produces exactly one mapping and
      does not include `.agents/skills/` from the packaged default.
- [ ] A missing custom config path raises `MappingConfigError` and does not fall
      back to the packaged default.
- [ ] Invalid TOML raises `MappingConfigError` with enough context to identify
      the file and parse failure.
- [ ] Schema-invalid TOML raises `MappingConfigError` while preserving Pydantic
      validation locations such as `mappings.0.path`.
- [ ] Unknown fields, invalid `keep_mode`, empty paths, and absolute paths all
      raise `MappingConfigError` when encountered through the loader, not just
      when testing models directly.
- [ ] A custom config path is read with UTF-8 encoding.
- [ ] An unreadable custom config file raises `MappingConfigError` if the test
      environment can reliably simulate permissions; otherwise cover the same
      error branch with a monkeypatched read failure.
- [ ] The loader does not inspect whether declarative source/destination paths
      exist on the local machine.

### Task 5: Wire CLI config path precedence into task generation

#### 5.1 Intent

Expose `--config PATH`, honor `SYNC_LISTING_CONFIG`, and pass the resolved
mapping list into existing task generation instead of importing a hardcoded
list.

#### 5.2 Files

- Modify: `src/sync_ai_config/cli.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_sync_tasks.py`

#### 5.3 Dependencies

Task 4.

- [ ] **Step 1:** Add `config: str | None = None` to `CliArgs`.
- [ ] **Step 2:** Add `--config PATH` with no short alias. Help text should say
      the file is TOML, overrides `SYNC_LISTING_CONFIG`, and replaces the
      packaged defaults.
- [ ] **Step 3:** Add a small documented resolver, for example
      `mapping_config_path_from_args(args: CliArgs) -> Path | None`, with
      precedence: CLI `--config` > `SYNC_LISTING_CONFIG` > packaged default.
- [ ] **Step 4:** Apply `Path(value).expanduser()` to CLI/env custom paths and
      leave relative paths relative to the current working directory.
- [ ] **Step 5:** In `main()`, after runtime config and operation validation but
      before constructing or using `TaskBuilder`, load mappings and catch
      `MappingConfigError` with `parser.error(str(exc))`.
- [ ] **Step 6:** Replace `ALL_FILE_MAPPINGS` usage with the loaded `mappings`
      list for both push and pull.
- [ ] **Step 7:** Add debug/info logging that identifies whether the packaged
      default or a custom config path is used, without logging excessive config
      contents.
- [ ] **Step 8:** Add tests proving `--config` beats `SYNC_LISTING_CONFIG`,
      `SYNC_LISTING_CONFIG` beats the packaged default, and existing commands
      still work without a config path.
- [ ] **Step 9:** Update existing sync-task tests to load the packaged default
      via the new loader instead of importing `ALL_FILE_MAPPINGS`.

#### 5.4 Verification

- Run: `uv run pytest tests/test_cli.py tests/test_sync_tasks.py -v`
- Run: `uv run pytest tests -v`
- Expect: CLI precedence and default behavior are covered, dry-run task output
  remains compatible, and no test imports a hardcoded mapping list.

#### 5.5 Notes

- Existing `main()` checks `rsync` before building config. Tests that invoke
  `main()` should monkeypatch `shutil.which` or avoid `main()` when only testing
  resolver behavior.
- For dry-run integration tests, set `SYNC_USER` and `SYNC_HOST` or pass
  `--remote-user`/`--remote-host` so runtime config validation does not mask
  mapping config assertions.

### Task 6: Update package-data and executable bundling paths

#### 6.1 Intent

Ensure `importlib.resources` can find `default_mappings.toml` in editable/wheel
installs and PyInstaller one-file builds.

#### 6.2 Files

- Modify: `pyproject.toml`
- Modify: `justfile`
- Modify: `sync-ai-config.spec`
- Test/Verify: built wheel artifact under `dist/`

#### 6.3 Dependencies

Task 3.

- [ ] **Step 1:** Add an explicit Hatchling wheel package-data entry, using a
      target-specific force include if needed, for example:
      `"src/sync_ai_config/default_mappings.toml" = "sync_ai_config/default_mappings.toml"`.
- [ ] **Step 2:** If the project builds source distributions, include the TOML
      resource there as well or verify Hatchling's default sdist includes
      package files under `src/sync_ai_config`.
- [ ] **Step 3:** Update `justfile` `build-exe` to pass
      `--add-data src/sync_ai_config/default_mappings.toml:sync_ai_config` to
      PyInstaller.
- [ ] **Step 4:** Update `sync-ai-config.spec` `datas` to include
      `("src/sync_ai_config/default_mappings.toml", "sync_ai_config")` so the
      spec path and justfile path stay aligned.
- [ ] **Step 5:** Run `uv build` and inspect the wheel with
      `uv run python -m zipfile -l dist/<wheel-name>.whl` or an equivalent
      command to confirm the TOML resource is inside `sync_ai_config/`.
- [ ] **Step 6:** If time and environment allow, run `just build-exe` and smoke
      test the generated binary with `--version` or a dry-run custom config.

#### 6.4 Verification

- Run: `uv build`
- Run: `uv run python -m zipfile -l dist/<wheel-name>.whl`
- Optional run: `just build-exe`
- Expect: The wheel and bundled executable include
  `sync_ai_config/default_mappings.toml`, and resource loading does not rely on
  repository source paths.

#### 6.5 Notes

- Keep this task after the resource file exists; packaging changes are otherwise
  easy to mistype and hard to verify.
- If both justfile and spec remain in the repository, update both to avoid two
  divergent build workflows.

### Task 7: Update user-facing and common documentation

#### 7.1 Intent

Document the new config file behavior for users and update project design notes
so future agents do not think mappings are still hardcoded.

#### 7.2 Files

- Modify: `README.md`
- Modify: `common-doc/design-doc-draft.md`

#### 7.3 Dependencies

Tasks 3 through 5.

- [ ] **Step 1:** In `README.md`, add `SYNC_LISTING_CONFIG` to quick setup as
      optional and document `--config PATH` in the command-line options table.
- [ ] **Step 2:** Add a short “Mapping config file” section to `README.md`
      explaining:
  - default packaged mappings are used when no config path is provided;
  - custom config replaces defaults entirely;
  - precedence is `--config` > `SYNC_LISTING_CONFIG` > packaged default;
  - the file is TOML and has no `version` field.
- [ ] **Step 3:** Include a concise TOML example with one file mapping and one
      directory mapping, showing `path`, optional `windows_path`/`remote_path`,
      `keep_mode`, `is_directory`, and `description`.
- [ ] **Step 4:** Document validation basics: paths must be relative fragments,
      unknown fields are rejected, and `keep_mode` must be one of
      `prefer_windows`, `prefer_linux`, or `keep_both`.
- [ ] **Step 5:** Update `common-doc/design-doc-draft.md` introduction/key logic
      to say mappings are now loaded from a packaged default TOML or a custom
      config file, rather than being hardcoded in Python.
- [ ] **Step 6:** Decide whether the long rsync examples in the design draft
      need a small note that they reflect the packaged default mapping config;
      avoid a large rewrite unless implementation changes their behavior.

#### 7.4 Verification

- Run: `uv run ruff check .` for code-related docstring/string lint side
  effects, if any.
- Optional run before finalizing: markdownlint if available or the
  `markdownlint-writer` skill when preparing for a commit/final handoff.
- Expect: Docs accurately describe the new option and do not imply the mapping
  list is hardcoded.

#### 7.5 Notes

- Keep documentation examples short; the full default mapping list lives in the
  packaged TOML file.
- Follow the existing README tone and table style.

### Task 8: Final integrated verification and cleanup

#### 8.1 Intent

Prove the implementation works end-to-end, remove temporary compatibility code,
and prepare a clean handoff for review or commit.

#### 8.2 Files

- Review: all modified source, tests, docs, packaging files, and lockfile

#### 8.3 Dependencies

Tasks 1 through 7.

- [ ] **Step 1:** Run `just test`.
- [ ] **Step 2:** Run `just typecheck`.
- [ ] **Step 3:** Run `just lint`.
- [ ] **Step 4:** Run `uv build` and inspect the wheel for
      `sync_ai_config/default_mappings.toml`.
- [ ] **Step 5:** Optionally run `just build-exe` if PyInstaller is available
      and not too slow; otherwise document that the packaging metadata was
      updated and wheel resource loading was verified.
- [ ] **Step 6:** Run `git diff --check` and `git status --short`.
- [ ] **Step 7:** Review the final diff for accidental hardcoded mapping-list
      remnants, especially imports or references to `ALL_FILE_MAPPINGS`.
- [ ] **Step 8:** Confirm user-facing errors for missing/invalid custom configs
      are clear and occur before task-building starts.

#### 8.4 Verification

- Run: `just test`
- Run: `just typecheck`
- Run: `just lint`
- Run: `uv build`
- Run: `git diff --check`
- Expect: All mandatory checks pass; wheel contains the default TOML resource;
  no runtime code depends on hardcoded mapping lists.

#### 8.5 Notes

- If type checking exposes Pydantic-related typing issues, prefer localized type
  annotations or helper return types over broad ignores.
- If any check fails due to an unrelated pre-existing issue, capture the exact
  command and failure in the final handoff.

## References

<!-- markdownlint-disable MD013 -->

| Resource                                                                     | Description                                                                                                                    | Other Notes if any |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| [GitHub issue #10](https://github.com/CXwudi/sync-ai-agent-config/issues/10) | Source ticket requesting configurable sync files/folders instead of hardcoded mappings.                                        | Must Read          |
| ![a file](spec/spec-configurable-sync-mappings-20260423.md:1:288)            | Approved design spec defining TOML + Pydantic, default packaging, CLI precedence, validation, tests, and non-goals.            | Must Read          |
| ![a file](AGENTS.md:1:30)                                                    | Repository instructions requiring documentation-first work, 2-space indentation, `uv run`, and clarification when needed.      | Important          |
| ![a file](common-doc/design-doc-draft.md:1:212)                              | Existing design notes describing current sync behavior and rsync examples that should be updated after config loading changes. | Important          |
| ![a file](src/sync_ai_config/models.py:18:63)                                | Current `KeepMode`, `FileMapping`, and `RsyncTask` definitions; `FileMapping` will become a Pydantic model.                    | Must Read          |
| ![a file](src/sync_ai_config/mappings.py:1:246)                              | Current hardcoded active mapping lists that must be translated exactly into packaged TOML defaults.                            | Must Read          |
| ![a file](src/sync_ai_config/cli.py:37:206)                                  | CLI argument parsing and task-building flow that must load mappings from config before passing them to `TaskBuilder`.          | Important          |
| ![a file](src/sync_ai_config/task_builder.py:1:241)                          | Existing mapping-to-rsync-task behavior that should remain unchanged except for type-hint modernization if needed.             | Important          |
| ![a file](src/sync_ai_config/task_executor.py:1:66)                          | Directory trailing-slash behavior that must keep working for `is_directory = true` mappings.                                   | Important          |
| ![a file](tests/test_sync_tasks.py:1:108)                                    | Existing tests asserting default task output and order; update them to use loaded default mappings.                            | Important          |
| ![a file](README.md:1:68)                                                    | User-facing setup, usage, and command option docs that need `--config`/`SYNC_LISTING_CONFIG` coverage.                         | Important          |
| ![a file](pyproject.toml:1:31)                                               | Project dependency and Hatchling build configuration; add Pydantic and include the default TOML resource.                      | Important          |
| ![a file](justfile:17:19)                                                    | PyInstaller build command that must include the packaged default TOML resource.                                                | Important          |
| ![a file](sync-ai-config.spec:4:16)                                          | Existing PyInstaller spec with empty `datas`; add the TOML resource if this build path remains.                                | Important          |

<!-- markdownlint-enable MD013 -->
