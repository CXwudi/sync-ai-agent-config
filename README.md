# 🤖 AI Agent Config Sync

Hey there! This is a helper tool to keep your AI agent configuration files (Claude, Gemini, etc.) synced across Linux, Windows, and a remote server.

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
export SYNC_DIR="~/sync-files/ai-agents-related" # Optional: default is ~/sync-files/ai-agents-related
export WIN_USER="your_windows_username" # e.g., "jane" if your windows path is /mnt/c/Users/jane
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

## Development

```bash
uv sync
just test       # Run tests
just typecheck  # Type check with ty
just lint       # Lint with ruff
just format     # Format with black
just build-exe  # Build a single-file executable
```

## Notes

- The legacy script is now `sync-ai-config-old.py`.

## Command-Line Options

| Argument | Flag | Environment Variable | Description |
|---|---|---|---|
| **Operation** | `push` or `pull` | | The sync operation to perform. |
| **Remote User** | `-u`, `--remote-user` | `SYNC_USER` | Your SSH username for the remote server. |
| **Remote Host** | `-H`, `--remote-host` | `SYNC_HOST` | The hostname or IP address of the remote server. |
| **Remote Dir** | `-d`, `--remote-dir` | `SYNC_DIR` | The base directory on the remote server to sync to. |
| **Windows User**| `-w`, `--windows-user`| `WIN_USER` | Your Windows username to enable syncing Windows files. |
| **Dry Run** | `--dry-run` | | Show what commands will be run without actually executing them. |
| **Rsync Opts** | `--rsync-opts` | | A string of options to pass directly to `rsync`. |
| **Log Level** | `--log-level` | | Set the logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| **Version** | `--version` | | Show the script's version. |
