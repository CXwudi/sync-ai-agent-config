# Draft Design Document

This program is a command-line utility to synchronize AI agent configuration files between a local machine (Linux/WSL and Windows) and a remote server. It supports push and pull operations for Claude Code and Gemini CLI configurations.

The script is designed to be run from a Linux environment (typically via WSL). To backup configurations from a Windows machine, specify the Windows username. Then, the script accesses the Windows files via the `/mnt/c/` path from WSL.

## Key operations and logic:

The program is a CLI utility with two main subcommands: `push` and `pull`. It includes options for specifying remote user, host, and Windows user

Only when the Windows user is specified, the Windows-specific operations are performed.

**push**:

- Copies configuration files from the local machine to the remote server.
- For some configuration files, the script first copies the versions from the Windows user's directory to the Linux home directory. Then pushed to the remote server. This ensures the Windows version is the source of truth.
- The script itself is also pushed to the remote server for easy access.

```sh
# Claude Code
rsync -avzL ~/.claude.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json
rsync -avzL /mnt/c/Users/{WIN_USER}/.claude.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json

rsync -avzL ~/.claude/settings.json /mnt/c/Users/{WIN_USER}/.claude/settings.json
rsync -avzL ~/.claude/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/settings.json

rsync -avzL ~/.claude/CLAUDE.md /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md
rsync -avzL ~/.claude/CLAUDE.md {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md

rsync -avzL ~/.claude/agents/ /mnt/c/Users/{WIN_USER}/.claude/agents/
rsync -avzL ~/.claude/agents/ {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/

rsync -avzL ~/.claude/skills/ /mnt/c/Users/{WIN_USER}/.claude/skills/
rsync -avzL ~/.claude/skills/ {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/skills/

# Gemini CLI
rsync -avzL ~/.gemini/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.linux.json
rsync -avzL /mnt/c/Users/{WIN_USER}/.gemini/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.windows.json

rsync -avzL /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md ~/.gemini/GEMINI.md
rsync -avzL ~/.gemini/GEMINI.md {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md

rsync -avzL ~/.gemini/skills/ /mnt/c/Users/{WIN_USER}/.gemini/skills/
rsync -avzL ~/.gemini/skills/ {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/skills/

# Codex
rsync -avzL ~/.codex/config.toml {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.linux.toml
rsync -avzL /mnt/c/Users/{WIN_USER}/.codex/config.toml {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.windows.toml

rsync -avzL ~/.codex/auth.json /mnt/c/Users/{WIN_USER}/.codex/auth.json
rsync -avzL ~/.codex/auth.json {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/auth.json

rsync -avzL /mnt/c/Users/{WIN_USER}/.codex/AGENTS.md ~/.codex/AGENTS.md
rsync -avzL ~/.codex/AGENTS.md {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/AGENTS.md

rsync -avzL ~/.codex/skills/ /mnt/c/Users/{WIN_USER}/.codex/skills/
rsync -avzL ~/.codex/skills/ {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/skills/

# OpenCode
rsync -avzL ~/.config/opencode/opencode.json /mnt/c/Users/{WIN_USER}/.config/opencode/opencode.json
rsync -avzL ~/.config/opencode/opencode.json {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/opencode.json

rsync -avzL ~/.config/opencode/opencode.jsonc /mnt/c/Users/{WIN_USER}/.config/opencode/opencode.jsonc
rsync -avzL ~/.config/opencode/opencode.jsonc {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/opencode.jsonc

rsync -avzL ~/.config/opencode/AGENTS.md /mnt/c/Users/{WIN_USER}/.config/opencode/AGENTS.md
rsync -avzL ~/.config/opencode/AGENTS.md {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/AGENTS.md

rsync -avzL ~/.config/opencode/prompts/ /mnt/c/Users/{WIN_USER}/.config/opencode/prompts/
rsync -avzL ~/.config/opencode/prompts/ {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/prompts/

rsync -avzL ~/.config/opencode/agents/ /mnt/c/Users/{WIN_USER}/.config/opencode/agents/
rsync -avzL ~/.config/opencode/agents/ {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/agents/

rsync -avzL ~/.config/opencode/commands/ /mnt/c/Users/{WIN_USER}/.config/opencode/commands/
rsync -avzL ~/.config/opencode/commands/ {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/commands/

rsync -avzL ~/.config/opencode/plugins/ /mnt/c/Users/{WIN_USER}/.config/opencode/plugins/
rsync -avzL ~/.config/opencode/plugins/ {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/plugins/

rsync -avzL ~/.local/share/opencode/auth.json /mnt/c/Users/{WIN_USER}/.local/share/opencode/auth.json
rsync -avzL ~/.local/share/opencode/auth.json {USER}@{HOST}:~/sync-files/ai-agents-related/.local/share/opencode/auth.json

# Cline
rsync -avzL ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.linux.json
rsync -avzL /mnt/c/Users/{WIN_USER}/AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.windows.json

rsync -avzL /mnt/c/Users/{WIN_USER}/Documents/Cline/Rules/ ~/Cline/Rules/
rsync -avzL ~/Cline/Rules/ {USER}@{HOST}:~/sync-files/ai-agents-related/Cline/Rules/
```

**pull**:

- Copies configuration files from the remote server to the local machine.
- Copies to both the Linux and Windows directories, ensuring both environments are synchronized.

```sh
# Claude Code
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json ~/.claude.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/ ~/.claude/agents/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/settings.json ~/.claude/settings.json

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json /mnt/c/Users/{WIN_USER}/.claude.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/ /mnt/c/Users/{WIN_USER}/.claude/agents/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/settings.json /mnt/c/Users/{WIN_USER}/.claude/settings.json

# Gemini CLI
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.linux.json ~/.gemini/settings.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md ~/.gemini/GEMINI.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/skills/ ~/.gemini/skills/

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.windows.json /mnt/c/Users/{WIN_USER}/.gemini/settings.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/skills/ /mnt/c/Users/{WIN_USER}/.gemini/skills/

# Codex
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.linux.toml ~/.codex/config.toml
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/auth.json ~/.codex/auth.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/AGENTS.md ~/.codex/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/skills/ ~/.codex/skills/

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.windows.toml /mnt/c/Users/{WIN_USER}/.codex/config.toml
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/auth.json /mnt/c/Users/{WIN_USER}/.codex/auth.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/AGENTS.md /mnt/c/Users/{WIN_USER}/.codex/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/skills/ /mnt/c/Users/{WIN_USER}/.codex/skills/

# OpenCode
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/opencode.json ~/.config/opencode/opencode.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/opencode.jsonc ~/.config/opencode/opencode.jsonc
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/AGENTS.md ~/.config/opencode/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/prompts/ ~/.config/opencode/prompts/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/agents/ ~/.config/opencode/agents/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/commands/ ~/.config/opencode/commands/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/plugins/ ~/.config/opencode/plugins/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.local/share/opencode/auth.json ~/.local/share/opencode/auth.json

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/opencode.json /mnt/c/Users/{WIN_USER}/.config/opencode/opencode.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/opencode.jsonc /mnt/c/Users/{WIN_USER}/.config/opencode/opencode.jsonc
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/AGENTS.md /mnt/c/Users/{WIN_USER}/.config/opencode/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/prompts/ /mnt/c/Users/{WIN_USER}/.config/opencode/prompts/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/agents/ /mnt/c/Users/{WIN_USER}/.config/opencode/agents/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/commands/ /mnt/c/Users/{WIN_USER}/.config/opencode/commands/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.config/opencode/plugins/ /mnt/c/Users/{WIN_USER}/.config/opencode/plugins/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.local/share/opencode/auth.json /mnt/c/Users/{WIN_USER}/.local/share/opencode/auth.json

# Cline
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/Cline/Rules/ ~/Cline/Rules/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.linux.json ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/Cline/Rules/ /mnt/c/Users/{WIN_USER}/Documents/Cline/Rules/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.windows.json /mnt/c/Users/{WIN_USER}/AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

## Others

The CLI contains one option, `--rsync-opts`, to pass custom options to rsync. By default, it uses `-avzL --update --delete --human-readable --mkpath`.
