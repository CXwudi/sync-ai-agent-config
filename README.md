# 🤖 AI Agent Config Sync

Hey there! This is a helper tool to keep your AI agent configuration files
(Claude, Gemini, etc.) synced across Linux, Windows, and a remote server.

It uses `rsync` under the hood.

## Prerequisites

- `rsync` (>= 3.2.3, for `--mkpath` support)
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just) (for development)

## Quick Setup

Set these environment variables so the tool knows where to sync:

```bash
export SYNC_USER="your_remote_username"
export SYNC_HOST="your_remote_hostname_or_ip"
export SYNC_DIR="~/sync-files/ai-agents-related" # default is ~/sync-files/ai-agents-related
export WIN_USER="your_windows_username" # Optional: e.g., "jane" if your windows path is /mnt/c/Users/jane
export SYNC_LISTING_CONFIG="~/sync-ai-mappings.toml" # Optional: file containing your custom list of files/folders to sync
```

## Usage

The two main commands are `push` and `pull`.

### Pushing Changes to Remote

```bash
uv run sync-ai-config push
```

### Pulling Changes from Remote

```bash
uv run sync-ai-config pull
```

### Example: Dry Run

```bash
uv run sync-ai-config push --dry-run
```

## Mapping Config File

By default, `sync-ai-config` comes with a default TOML mapping file for the
supported agent configs. You can replace it with your own by creating a custom
mapping config as follows:

Example:

```toml
[[mappings]]
# Required path relative to the Linux home directory.
# Also used as the default Windows and remote path when no override is provided.
path = ".codex/plugins/"

# Optional path relative to /mnt/c/Users/{WIN_USER}.
# Omit this when the Windows-side path is the same as path.
windows_path = ".codex/plugins/"

# Optional path relative to SYNC_DIR.
# Omit this when the remote-side path is the same as path.
remote_path = ".codex/plugins/"

# Required sync mode: prefer_windows, prefer_linux, or keep_both.
keep_mode = "prefer_linux"

# Optional; defaults to false.
# Set true for directory mappings so rsync paths keep trailing slashes.
is_directory = true

# Optional human-readable label used in logs.
description = "Codex plugins"

[[mappings]]
# your next mapping and so on
```

Then either set the `SYNC_LISTING_CONFIG` env var, or pass the path with
`--config` when running the command:

```bash
uv run sync-ai-config push --config ~/my-sync-mappings.toml
```

## Development

```bash
uv sync
just test       # Run tests
just typecheck  # Type check with ty
just lint       # Lint with ruff
just format     # Format with ruff
just build-exe  # Build a single-file executable
```

## Notes

- The legacy script is now `sync-ai-config-old.py`.

## Command-Line Options

<!-- markdownlint-disable MD013 -->

| Argument           | Flag                   | Environment Variable  | Description                                                      |
| ------------------ | ---------------------- | --------------------- | ---------------------------------------------------------------- |
| **Operation**      | `push` or `pull`       |                       | The sync operation to perform.                                   |
| **Remote User**    | `-u`, `--remote-user`  | `SYNC_USER`           | Your SSH username for the remote server.                         |
| **Remote Host**    | `-H`, `--remote-host`  | `SYNC_HOST`           | The hostname or IP address of the remote server.                 |
| **Remote Dir**     | `-d`, `--remote-dir`   | `SYNC_DIR`            | The base directory on the remote server to sync to.              |
| **Windows User**   | `-w`, `--windows-user` | `WIN_USER`            | Your Windows username to enable syncing Windows files.           |
| **Mapping Config** | `--config`             | `SYNC_LISTING_CONFIG` | TOML mapping config that replaces the packaged defaults.         |
| **Dry Run**        | `--dry-run`            |                       | Show what commands will be run without actually executing them.  |
| **Rsync Opts**     | `--rsync-opts`         |                       | A string of options to pass directly to `rsync`.                 |
| **Log Level**      | `--log-level`          |                       | Set the logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| **Version**        | `--version`            |                       | Show the script's version.                                       |

<!-- markdownlint-enable MD013 -->
