# Draft Design Document

This program is a command-line utility to synchronize AI agent configuration
files between a local machine (Linux/WSL and Windows) and a remote server. It
supports push and pull operations for Claude Code, Gemini CLI, Codex, Pi Coding
Agent, OpenCode, and Cline configurations.

The sync file/folder mappings are loaded from a packaged default TOML file by
default. Users can provide a custom TOML mapping config with `--config PATH` or
`SYNC_LISTING_CONFIG`; a custom config replaces the packaged mapping list
entirely.

The script is designed to be run from a Linux environment (typically via WSL).
To backup configurations from a Windows machine, specify the Windows username.
Then, the script accesses the Windows files via the `/mnt/c/` path from WSL.

## Key operations and logic

The program is a CLI utility with two main subcommands: `push` and `pull`. It
includes options for specifying remote user, host, Windows user, and an optional
custom mapping config path.

Only when the Windows user is specified, the Windows-specific operations are
performed. When no custom mapping config is specified, the packaged default
mappings are used. Custom config path precedence is `--config PATH`, then
`SYNC_LISTING_CONFIG`, then the packaged default mapping file.

The long `rsync` examples below describe the packaged default mapping config.
Custom mapping configs can generate a different file/folder list while keeping
the same push and pull task-generation rules.

**push**:

- Copies configuration files from the local machine to the remote server.
- For some configuration files, the script first copies the versions from the
  Windows user's directory to the Linux home directory and then pushes them to
  the remote server. This ensures the Windows version is the source of truth.
- The script syncs the shared `~/.agents/skills/` directory for agents that use
  the common skills location, while Claude Code keeps syncing its dedicated
  `~/.claude/skills/` directory.
- The script executes all generated `rsync` commands even if some fail. Any
  non-zero `rsync` exit code still causes the overall command to fail.
- The script itself is also pushed to the remote server for easy access.

<!-- markdownlint-disable MD013 -->

```sh
# Common for Agents
rsync -avzL ~/.agents/skills/ /mnt/c/Users/{WIN_USER}/.agents/skills/
rsync -avzL ~/.agents/skills/ {USER}@{HOST}:~/sync-files/ai-agents-related/.agents/skills/

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

rsync -avzL /mnt/c/Users/{WIN_USER}/.gemini/AGENTS.md ~/.gemini/AGENTS.md
rsync -avzL ~/.gemini/AGENTS.md {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/AGENTS.md

rsync -avzL /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md ~/.gemini/GEMINI.md
rsync -avzL ~/.gemini/GEMINI.md {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md

# Codex
rsync -avzL ~/.codex/config.toml {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.linux.toml
rsync -avzL /mnt/c/Users/{WIN_USER}/.codex/config.toml {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.windows.toml

rsync -avzL ~/.codex/auth.json /mnt/c/Users/{WIN_USER}/.codex/auth.json
rsync -avzL ~/.codex/auth.json {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/auth.json

rsync -avzL /mnt/c/Users/{WIN_USER}/.codex/AGENTS.md ~/.codex/AGENTS.md
rsync -avzL ~/.codex/AGENTS.md {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/AGENTS.md

rsync -avzL ~/.codex/plugins/ /mnt/c/Users/{WIN_USER}/.codex/plugins/
rsync -avzL ~/.codex/plugins/ {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/plugins/

# Pi Coding Agent
rsync -avzL ~/.pi/agent/settings.json /mnt/c/Users/{WIN_USER}/.pi/agent/settings.json
rsync -avzL ~/.pi/agent/settings.json {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/settings.json

rsync -avzL ~/.pi/agent/auth.json /mnt/c/Users/{WIN_USER}/.pi/agent/auth.json
rsync -avzL ~/.pi/agent/auth.json {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/auth.json

rsync -avzL ~/.pi/agent/AGENTS.md /mnt/c/Users/{WIN_USER}/.pi/agent/AGENTS.md
rsync -avzL ~/.pi/agent/AGENTS.md {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/AGENTS.md

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

<!-- markdownlint-enable MD013 -->

**pull**:

- Copies configuration files from the remote server to the local machine.
- Copies to both the Linux and Windows directories, ensuring both environments
  are synchronized.

<!-- markdownlint-disable MD013 -->

```sh
# Common for Agents
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.agents/skills/ ~/.agents/skills/
rsync -avzL ~/.agents/skills/ /mnt/c/Users/{WIN_USER}/.agents/skills/

# Claude Code
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.linux.json ~/.claude.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/ ~/.claude/agents/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/skills/ ~/.claude/skills/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/settings.json ~/.claude/settings.json

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude.windows.json /mnt/c/Users/{WIN_USER}/.claude.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/CLAUDE.md /mnt/c/Users/{WIN_USER}/.claude/CLAUDE.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/agents/ /mnt/c/Users/{WIN_USER}/.claude/agents/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/skills/ /mnt/c/Users/{WIN_USER}/.claude/skills/
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.claude/settings.json /mnt/c/Users/{WIN_USER}/.claude/settings.json

# Gemini CLI
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.linux.json ~/.gemini/settings.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/AGENTS.md ~/.gemini/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md ~/.gemini/GEMINI.md

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/settings.windows.json /mnt/c/Users/{WIN_USER}/.gemini/settings.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/AGENTS.md /mnt/c/Users/{WIN_USER}/.gemini/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.gemini/GEMINI.md /mnt/c/Users/{WIN_USER}/.gemini/GEMINI.md

# Codex
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.linux.toml ~/.codex/config.toml
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/auth.json ~/.codex/auth.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/AGENTS.md ~/.codex/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/plugins/ ~/.codex/plugins/

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/config.windows.toml /mnt/c/Users/{WIN_USER}/.codex/config.toml
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/auth.json /mnt/c/Users/{WIN_USER}/.codex/auth.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/AGENTS.md /mnt/c/Users/{WIN_USER}/.codex/AGENTS.md
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.codex/plugins/ /mnt/c/Users/{WIN_USER}/.codex/plugins/

# Pi Coding Agent
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/settings.json ~/.pi/agent/settings.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/auth.json ~/.pi/agent/auth.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/AGENTS.md ~/.pi/agent/AGENTS.md

rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/settings.json /mnt/c/Users/{WIN_USER}/.pi/agent/settings.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/auth.json /mnt/c/Users/{WIN_USER}/.pi/agent/auth.json
rsync -avzL {USER}@{HOST}:~/sync-files/ai-agents-related/.pi/agent/AGENTS.md /mnt/c/Users/{WIN_USER}/.pi/agent/AGENTS.md

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

<!-- markdownlint-enable MD013 -->

## Others

The CLI contains one option, `--rsync-opts`, to pass custom options to rsync. By
default, it uses `-avzL --update --delete --human-readable --mkpath`.
