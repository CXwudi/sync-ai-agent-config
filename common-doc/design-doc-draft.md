# Draft Design Document

This program is a command-line utility to synchronize AI agent configuration files between a local machine (Linux/WSL and Windows) and a remote server. It supports push and pull operations for Claude Code and Gemini CLI configurations.

The script is designed to be run from a Linux environment (including WSL). When a Windows user is specified, it accesses Windows files via the `/mnt/c/` path from WSL.

## Key operations and logic:

**push**:

- Copies configuration files from the local machine to the remote server.
- For `CLAUDE.md`, `GEMINI.md`, and Claude Code subagents at `~/.claude/agents`, the script first copies the versions from the Windows user's directory to the Linux home directory. This consolidated version is then pushed to the remote server. This ensures the Windows version is the source of truth.
- The script itself is also pushed to the remote server for easy access.

```sh
# Claude Code
rsync -avz ~/.claude.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json
rsync -avz /mnt/c/Users/{WIN_USER}/.claude.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json

rsync -avz /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avz ~/.claude/CLAUDE.md {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md

rsync -avz /mnt/c/Users/{WIN_USER}/.claude/agents/ ~/.claude/agents/
rsync -avz ~/.claude/agents/ {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/

# Gemini CLI
rsync -avz ~/.gemini/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.linux.json
rsync -avz /mnt/c/Users/{WIN_USER}/.gemini/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.windows.json

rsync -avz /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md ~/.gemini/GEMINI.md
rsync -avz ~/.gemini/GEMINI.md {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md
```

**pull**:

- Copies configuration files from the remote server to the local machine.
- Copies to both the Linux and Windows directories, ensuring both environments are synchronized.

```sh
# Claude Code
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json ~/.claude.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/ ~/.claude/agents/

rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json /mnt/c/Users/{WIN_USER}/.claude.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/ /mnt/c/Users/{WIN_USER}/.claude/agents/

# Gemini CLI
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.linux.json ~/.gemini/settings.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md ~/.gemini/GEMINI.md

rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.windows.json /mnt/c/Users/{WIN_USER}/.gemini/settings.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md
```

The program is a CLI utility with two main subcommands: `push` and `pull`. It includes options for specifying remote user, host, and Windows user, as well as flags for dry runs, uses `rsync` with the `--update` flag (enabled by default) and verbose output.

Only when the Windows user is specified, the Windows-specific operations are performed.
