# shanewas-plugins

Universal multi-agent plugin and skill marketplace by **Shanewas Ahmed**.

Supports **Claude Code**, **Google Antigravity**, **OpenCode**, **Hermes**, and **Muse Code**.

---

## 🚀 Quick Install

### 1. Claude Code
Register this marketplace repository in Claude Code:
```bash
claude plugin marketplace add shanewas/shanewas-plugins
```

Install any plugin from the marketplace:
```bash
claude plugin install core-tools@shanewas-plugins
```

### 2. Antigravity / Gemini CLI
Symlink or copy plugin directories into your global extensions or workspace:
```bash
# Global Antigravity extension
cp -r plugins/core-tools ~/.gemini/extensions/core-tools
```
Or register skills directly:
```bash
cp -r plugins/core-tools/skills/* ~/.gemini/config/skills/
```

### 3. OpenCode
In `~/.config/opencode/opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "./plugins/core-tools/plugin.js"
  ]
}
```

### 4. Hermes & Muse Code
Universal skills located under `plugins/<plugin>/skills/` conform to standard `SKILL.md` frontmatter. Simply point your skills directory to it:
- Hermes: copy or link into `~/.hermes/skills/` or `$HERMES_HOME/desktop-plugins/`
- Muse: copy or link into `~/.config/muse/skills/`

---

## 🛠️ Adding New Plugins

Scaffold a fully cross-compatible plugin in one command:

```powershell
./add-plugin.ps1 -Name "my-awesome-tool" -Description "Custom automation workflows" -Category "development"
```

This automatically generates:
- `.claude-plugin/plugin.json`
- `gemini-extension.json`
- `package.json` + `plugin.js`
- `skills/my-awesome-tool/SKILL.md`
- Updates root `.claude-plugin/marketplace.json`

---

## 📂 Repository Layout

```
shanewas-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Root marketplace catalog for Claude Code
├── plugins/
│   └── core-tools/               # Plugin bundle
│       ├── .claude-plugin/
│       │   └── plugin.json       # Claude Code plugin spec
│       ├── gemini-extension.json # Antigravity extension spec
│       ├── package.json          # OpenCode / Node package
│       ├── plugin.js             # OpenCode plugin entry point
│       ├── skills/               # Universal skills (compatible with all 5 agents)
│       │   └── git-summary/
│       │       └── SKILL.md
│       ├── commands/             # Slash commands (e.g. /summary)
│       └── agents/               # Specialized subagents (e.g. repo-auditor)
├── add-plugin.ps1                # Scaffolding helper script
├── AGENTS.md                     # Cross-agent guidelines
├── GEMINI.md                     # Antigravity rules
├── CLAUDE.md                     # Claude Code rules
└── LICENSE                       # MIT License
```

---

## 📄 License
MIT © [Shanewas Ahmed](https://github.com/shanewas)
