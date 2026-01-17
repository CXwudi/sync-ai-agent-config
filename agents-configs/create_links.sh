#!/bin/bash

# Directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Creating symlinks in $SCRIPT_DIR..."

# Function to create symlink
create_link() {
    local source=$1
    local name=$2
    local target="$SCRIPT_DIR/$name"

    # Expand tilde if present (though passing from main calls handles this mostly, proper expansion is safer)
    source="${source/#\~/$HOME}"

    if [ -e "$source" ] || [ -d "$source" ]; then
        echo "Linking $name -> $source"
        ln -sfn "$source" "$target"
    else
        echo "Warning: Source $source does not exist. Skipping $name."
    fi
}

# 1. ~/.claude.json
create_link "$HOME/.claude.json" ".claude.json"

# 2. ~/.claude/
create_link "$HOME/.claude" ".claude"

# 3. ~/.codex/
create_link "$HOME/.codex" ".codex"

# 4. ~/.gemini (Gemini CLI)
create_link "$HOME/.gemini" ".gemini"

# 5. ~/.config/opencode (Opencode)
create_link "$HOME/.config/opencode" "opencode"

# 6. Cline MCP settings json
# Using the path found in .vscode-server
CLINE_SETTINGS="$HOME/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
# Fallback for local vscode if server path fails
if [ ! -e "$CLINE_SETTINGS" ]; then
    CLINE_SETTINGS="$HOME/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
fi
create_link "$CLINE_SETTINGS" "cline_mcp_settings.json"

echo "Symlink creation complete."
