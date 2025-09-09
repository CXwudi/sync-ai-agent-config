# AI Configuration Sync Script

A simple, standalone Python script to synchronize AI agent configuration files between local machine and remote server using rsync.

## Overview

This repository contains `sync-ai-config.py` - a complete, working solution for syncing Claude Code and Gemini CLI configurations across Linux, Windows (via WSL), and remote servers.

**Note**: This project originally planned a complex OOP architecture with dependency injection (see `old-doc/design-doc.md`), but the standalone script approach proved far superior in simplicity and maintainability.

## Features

- **Bidirectional Sync**: Push local configs to remote or pull remote configs to local
- **Cross-Platform**: Supports Linux and Windows
  - To support Windows, the script must be run from WSL. The Windows files are accessed via the `/mnt/c/` path.
- **Smart Backup**: Timestamped backups before operations
- **File Protection**: Uses rsync `--update` by default to protect newer files
- **Comprehensive Logging**: Colored console output with file logging
- **Dry Run Support**: Preview operations without making changes
- **Connectivity Checks**: Validates SSH connection before operations

## Installation

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd sync-ai-config
   ```

2. Make the script executable:
   ```bash
   chmod +x sync-ai-config.py
   ```

3. Set up your configuration (see [Configuration](#configuration) section)

## Quick Start

### Using Environment Variables (Recommended)

Set up your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
export SYNC_USER="your-username"
export SYNC_HOST="your-server.com"
# Optional: for Windows file sync
export WIN_USER="YourWindowsUser"
```

Then run commands directly:
```bash
# Push local configs to remote
./sync-ai-config.py push

# Pull remote configs to local  
./sync-ai-config.py pull

# Dry run to see what would be synced
./sync-ai-config.py -n push

# Verbose pull with backup
./sync-ai-config.py -vb pull
```

### Using Command-Line Arguments

```bash
# Linux-only operation (no Windows files)
./sync-ai-config.py -u username -H server.example.com push

# Include Windows files
./sync-ai-config.py -u username -H server.example.com -w myuser push

# Check connectivity only
./sync-ai-config.py -u username -H server.example.com -c

# List all file mappings
./sync-ai-config.py -l
```

## Usage

```bash
./sync-ai-config.py [operation] [options]
```

### Operations
- `push` - Push local configs to remote server (default)
- `pull` - Pull remote configs to local machine

### Options
| Option | Description |
|---|---|
| `-u`, `--remote-user USER` | Remote SSH username (**required** if `SYNC_USER` not set) |
| `-H`, `--remote-host HOST` | Remote SSH host (**required** if `SYNC_HOST` not set) |
| `-d`, `--remote-dir DIR` | Remote directory path |
| `-w`, `--windows-user USER` | Windows username for `/mnt/c/` access (enables Windows operations) |
| `-v`, `--verbose` | Enable verbose output |
| `-q`, `--quiet` | Suppress non-error output |
| `-n`, `--dry-run` | Show what would be synced without doing it |
| `-b`, `--backup` | Create timestamped backup before sync |
| `-c`, `--check` | Only check connectivity |
| `-l`, `--list` | List all file mappings |
| `--config` | Show current configuration |

## Configuration

The script is configured via command-line arguments or environment variables. Command-line arguments always override environment variables.

| Parameter | CLI Argument | Environment Variable | Required | Default | Description |
|---|---|---|---|---|---|
| Remote User | `-u`, `--remote-user` | `SYNC_USER` | **Yes** | - | Your SSH username for the remote server |
| Remote Host | `-H`, `--remote-host` | `SYNC_HOST` | **Yes** | - | Hostname or IP address of the remote server |
| Remote Directory | `-d`, `--remote-dir` | `SYNC_DIR` | No | `~/sync-files/ai-agents-related` | Base directory on remote server for syncing files |
| Windows User | `-w`, `--windows-user` | `WIN_USER` | No | - | Windows username - enables Windows file operations when provided |

### File Synchronization

The script syncs a predefined set of AI agent configuration files. The exact files depend on your configuration.

#### Core Files (Always Synced)

| Local Path (Linux/WSL) | Remote Name | Description |
|---|---|---|
| `~/.claude.json` | `.claude.linux.json` | Claude CLI configuration |
| `~/.claude/CLAUDE.md` | `CLAUDE.md` | Claude global instructions |
| `~/.claude/agents/` | `agents/` | Claude subagents |
| `~/.gemini/settings.json` | `gemini.settings.linux.json` | Gemini CLI settings |
| `~/.gemini/GEMINI.md` | `GEMINI.md` | Gemini global instructions |
| `./sync-ai-config.py` | `sync-ai-config.py` | This sync script itself (push only) |

#### Conditional Windows Files (Only when `WIN_USER` provided)

| Local Path (Windows via WSL) | Remote Name | Description |
|---|---|---|
| `/mnt/c/Users/{WIN_USER}/.claude.json` | `.claude.windows.json` | Claude config from Windows |
| `/mnt/c/Users/{WIN_USER}/.gemini/settings.json` | `gemini.settings.windows.json` | Gemini settings from Windows |

**Note**: During `push`, Windows versions of `CLAUDE.md` and `GEMINI.md` are first copied to the Linux home directory (`~/.claude/` and `~/.gemini/`) before syncing to remote.

## Prerequisites

- **Python 3.8+**: Check with `python3 --version`
- **rsync**: Must be installed and in your system's PATH. Check with `rsync --version`
- **SSH Access**: Passwordless SSH access to the remote server (SSH keys recommended). Test with `ssh user@host`
- **WSL (for Windows users)**: Required to sync files from Windows user profile. Ensure your C: drive is mounted at `/mnt/c/`

## Why This Approach?

This project demonstrates that simple, direct solutions often outperform complex architectures:

- **✅ Working**: 590 lines of functional code vs unimplemented OOP framework
- **✅ Maintainable**: Single file vs dozens of classes and interfaces
- **✅ Understandable**: Clear flow vs abstraction layers
- **✅ Practical**: Solves the actual problem without over-engineering

The original design document (`old-doc/design-doc.md`) is preserved as a reference for what not to over-engineer.
