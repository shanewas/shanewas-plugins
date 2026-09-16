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
- `plugins/audit-trail/`: Zero-dependency edit ledger and review digest: log hook events to JSONL, render per-file digests.
- `plugins/commit-gate/`: Zero-dependency commit-message and staged-file gate: warn or block on bad shape, AI trailers, and banned extensions.
- `plugins/core-tools/`: Starter package with `git-summary` skill, `/summary` command, and audit agent
- `plugins/minimal-diff/`: Zero-dependency diff-size gate: warn or block when a change is too big for one review.
- `plugins/review-pair/`: Zero-dependency review-findings shape gate: warn or block when review lines are not machine-readable.
- `plugins/slop-gate/`: Zero-dependency AI-slop scorer and edit gate: warn or block on sloppy prose.
- `plugins/verify-done/`: Zero-dependency done-claim gate: warn or block when a done claim lacks build, test, or artifact evidence.
- `tests/`: Zero-dependency fixture tests, run with `python3 tests/run.py`
- `add-plugin.ps1`: PowerShell generator for new packages

## License
MIT

## Install Matrix (Unit 0)

Supported-harness overview. Install paths below are repo-observed (from
`## Installation` above and `.claude-plugin/marketplace.json`); no live
spike verification evidence was present in the unit-0 handoff, so the
Verified column stays TBD until a later unit exercises each harness.

| Harness | Install path (repo-observed) | Verified |
|---|---|---|
| Claude Code | `claude plugin marketplace add shanewas/shanewas-plugins`, then `claude plugin install core-tools@shanewas-plugins` | TBD |
| Muse Code | `muse plugins marketplace add shanewas-plugins https://github.com/shanewas/shanewas-plugins`, then `muse plugins install core-tools@shanewas-plugins`; refresh via `muse plugins marketplace update shanewas-plugins` | TBD |
| OpenCode | Reference `plugins/core-tools/plugin.js` in `plugin` list of `opencode.json` | TBD |
| Google Antigravity | Copy/mount `plugins/core-tools` into `~/.gemini/extensions/` (discovery via `gemini-extension.json`) | TBD |
| Hermes | Drop `plugins/<name>/skills/` folders into `~/.hermes/skills/` | TBD |
