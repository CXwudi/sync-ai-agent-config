This program is a command-line utility to synchronize AI agent configuration files between a local machine (Linux/WSL and Windows) and a remote server. It supports push and pull operations for Claude Code and Gemini CLI configurations.

The script is designed to be run from a Linux environment (including WSL). When a Windows user is specified, it accesses Windows files via the `/mnt/c/` path.

Key operations and logic:

push:
-   Copies configuration files from the local machine to the remote server.
-   For `CLAUDE.md` and `GEMINI.md`, the script first copies the versions from the Windows user's directory to the Linux home directory. This consolidated version is then pushed to the remote server. This ensures the Windows version is the source of truth.
-   The script itself is also pushed to the remote server for easy access.

```
# Claude Code
rsync -avz ~/.claude.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json
rsync -avz /mnt/c/Users/{WIN_USER}/.claude.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json
cp /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avz ~/.claude/CLAUDE.md {USER}@{HOST}:~/sync-files/ai-agents-related/CLAUDE.md

# Gemini CLI
rsync -avz ~/.gemini/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/gemini.settings.linux.json
rsync -avz /mnt/c/Users/{WIN_USER}/.gemini/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/gemini.settings.windows.json
cp /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md ~/.gemini/GEMINI.md
rsync -avz ~/.gemini/GEMINI.md {USER}@{HOST}:~/sync-files/ai-agents-related/GEMINI.md
```

pull:
-   Copies configuration files from the remote server to the local machine.
-   `CLAUDE.md` and `GEMINI.md` are pulled from the remote server to both the Linux and Windows directories, ensuring both environments are synchronized.

```
# Claude Code
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json ~/.claude.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/CLAUDE.md ~/.claude/CLAUDE.md

rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json /mnt/c/Users/{WIN_USER}/.claude.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/CLAUDE.md /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md

# Gemini CLI
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/gemini.settings.linux.json ~/.gemini/settings.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/GEMINI.md ~/.gemini/GEMINI.md

rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/gemini.settings.windows.json /mnt/c/Users/{WIN_USER}/.gemini/settings.json
rsync -avz {USER}@{HOST}:~/sync-files/ai-agents-related/GEMINI.md /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md
```

The program is a CLI utility with two main subcommands: `push` and `pull`. It includes options for specifying remote user, host, and Windows user, as well as flags for dry runs, backups, and verbose output.

The script checks for file existence before operations and uses `rsync` with the `--update` flag by default to avoid overwriting newer files.
