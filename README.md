# shanewas-plugins

Plugin and skill catalog for terminal coding agents, maintained by Shanewas Ahmed.

Packages in this repository follow the Anthropic Claude Code marketplace schema while keeping directory layouts directly mountable by Muse, Antigravity, and OpenCode.

## Installation

### Claude Code
Add the marketplace catalog:
```bash
claude plugin marketplace add shanewas/shanewas-plugins
```
Then install plugins by name:
```bash
claude plugin install core-tools@shanewas-plugins
```

### Muse Code
Register the Git source:
```bash
muse plugins marketplace add shanewas-plugins https://github.com/shanewas/shanewas-plugins
```
Install:
```bash
muse plugins install core-tools@shanewas-plugins
```
When new commits land upstream, sync the local snapshot with `muse plugins marketplace update shanewas-plugins`.

### OpenCode
Reference plugin entries directly in `~/.config/opencode/opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "C:/Personal/shanewas-plugins/plugins/core-tools/plugin.js"
  ]
}
```

### Google Antigravity
Mount the plugin directory inside `~/.gemini/extensions/` or copy skills into `~/.gemini/config/skills/`:
```bash
cp -r plugins/core-tools ~/.gemini/extensions/core-tools
```

### Hermes
Drop skill folders from `plugins/<name>/skills/` straight into `~/.hermes/skills/`.

## Creating a Plugin

The helper script sets up the cross-agent layout and registers the new entry into `.claude-plugin/marketplace.json`:

```powershell
./add-plugin.ps1 -Name "my-tool" -Description "Repo linting and release checks"
```

Each package folder contains:
- `.claude-plugin/plugin.json` for Claude Code and Muse manifest readers
- `gemini-extension.json` for Antigravity discovery
- `package.json` and `plugin.js` for OpenCode imports
- `skills/` with portable `SKILL.md` documents
- `commands/` and `agents/` for Claude slash commands and subagents

## Repository Layout

- `.claude-plugin/marketplace.json`: Root catalog listing available packages
- `plugins/core-tools/`: Starter package with `git-summary` skill, `/summary` command, and audit agent
- `add-plugin.ps1`: PowerShell generator for new packages

## License
MIT
