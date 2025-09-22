# 🤖 AI Agent Config Sync

Hey there! This is a little helper script to keep your AI agent configuration files (for Claude, Gemini, etc.) synced up between your different machines (Linux, Windows, and a remote server).

It uses `rsync` under the hood to make sure everything is in the right place.

## Prerequisites

Make sure you have `rsync` installed on your system. If not, you can usually get it with your system's package manager:

```bash
# On Debian/Ubuntu
sudo apt-get install rsync
```

## Quick Setup

For the script to know where to sync your files, you'll need to give it some details about your remote server and Windows username. The easiest way is to set these as environment variables.

You can add these to your `.bashrc` or `.zshrc` file:

```bash
export SYNC_USER="your_remote_username"
export SYNC_HOST="your_remote_hostname_or_ip"
export SYNC_DIR="~/sync-files/ai-agents-related" # Optional: default is ~/sync-files/ai-agents-related
export WIN_USER="your_windows_username" # e.g., "jane" if your windows path is /mnt/c/Users/jane
```

## How to Use

The two main commands are `push` and `pull`.

### Pushing Changes to Remote

When you've made changes locally and want to send them to the remote server, run:

```bash
uv run sync-ai-config.py push
```

### Pulling Changes from Remote

To grab the latest configs from the remote server and update your local machine(s), run:

```bash
uv run sync-ai-config.py pull
```

## Command-Line Options

You can also use command-line flags to override the environment variables or change the script's behavior.

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

### Example: Dry Run

If you want to see what the script is going to do without making any changes, use the `--dry-run` flag. This is super helpful for checking things!

```bash
uv run sync-ai-config.py push --dry-run
```

That's it! Happy syncing! ✨