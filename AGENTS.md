# AGENTS.md

Cross-agent guidance for shanewas-plugins repository.

## Identity Boundary
- Repository owner: Shanewas Ahmed (`@shanewas`)
- Author email: `shanewasahmed@gmail.com`
- Never mix with corporate identities or internal company credentials.

## Plugin Structure
All plugins live under `plugins/<name>/`.
Each plugin must provide:
- `.claude-plugin/plugin.json` (Claude Code)
- `gemini-extension.json` (Antigravity)
- `package.json` + `plugin.js` (OpenCode)
- `skills/<name>/SKILL.md` (Universal skill format)
