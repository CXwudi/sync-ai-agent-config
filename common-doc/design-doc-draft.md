This program simply just call a bunch of backup/download files related to ai agent config to/from a remote server.

command I have used:

```
rsync -avz /mnt/c/Users/11134/.claude.json cxwudi@5.78.95.153:~/sync-files/ai-agents-related/.claude.window.json
rsync -avz ~/.claude.json cxwudi@5.78.95.153:~/sync-files/ai-agents-related/.claude.linux.json
cp /mnt/c/Users/11134/.claude/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avz ~/.claude/CLAUDE.md cxwudi@5.78.95.153:~/sync-files/ai-agents-related/CLAUDE.md

rsync -avz ~/.gemini/settings.json cxwudi@5.78.95.153:~/sync-files/ai-agents-related/gemini.settings.wsl.json
rsync -avz /mnt/c/Users/11134/.gemini/settings.json cxwudi@5.78.95.153:~/sync-files/ai-agents-related/gemini.settings.window.json
```

```
rsync -avz cxwudi@5.78.95.153:~/sync-files/ai-agents-related/.claude.linux.json ~/.claude.json
rsync -avz cxwudi@5.78.95.153:~/sync-files/ai-agents-related/CLAUDE.md ~/.claude/CLAUDE.md
rsync -avz cxwudi@5.78.95.153:~/sync-files/ai-agents-related/.claude.window.json /mnt/c/Users/11134/.claude.json
rsync -avz cxwudi@5.78.95.153:~/sync-files/ai-agents-related/CLAUDE.md /mnt/c/Users/11134/.claude/CLAUDE.md

rsync -avz cxwudi@5.78.95.153:~/sync-files/ai-agents-related/gemini.settings.wsl.json ~/.gemini/settings.json
rsync -avz cxwudi@5.78.95.153:~/sync-files/ai-agents-related/gemini.settings.window.json /mnt/c/Users/11134/.gemini/settings.json
```

Basically backup and restoration of Claude Code and Gemini CLI.

Our program should be a CLI program, packaged as an executable using pyinstaller, and ran in linux env

CLI program contains two subcommands: backup and restore

backup of windows env from /mct/c/ is optional with a flag, and several other command line argument to specify the username in windows

when backup of windows env is specified, another flag is required to specify which CLAUDE.md (either windows or linux) to backup, and the selected also get copied to another env

Oh I just realize Gemini CLI also has a similar file of CLAUDE.md called GEMINI.md, live in ~/.gemini/GEMINI.md, I guess we will need to handle that too.

Handling of GEMINI should follow exactly same of CLAUDE.md, including the choosing of which env to backup and overwrite another env

when restoring, user can also use a flag to optionally restore windows env, but linux one is always restored
