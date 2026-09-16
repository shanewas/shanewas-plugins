---
name: minimal-diff
description: Use when a change needs a size check before review, when a diff should be gated on files touched or lines changed, or when a change spans more concerns than one review can hold.
---

# Minimal Diff

Gates each change on diff size: files touched, lines added plus
removed, and a concern proxy (the larger of distinct top-level
dirs and distinct file extensions). It warns by default and can
block when
`DIFF_GATE_MODE=block` is set. The tool is one Python file with no
third-party packages, so it runs anywhere Python 3.9 does.

## Limits

- More than 5 files trips the gate. One review, one handful of files.
- More than 400 added plus removed lines trips it. Big diffs hide bugs.
- A concern proxy over 3 trips it: max(distinct top-level dirs,
  distinct file extensions). Scattered changes split apart.

## Commands

```bash
git diff HEAD -- | python3 tools/diffgate.py check       # warn past a limit, exit 0
python3 tools/diffgate.py check CHANGES.diff             # check a saved diff file
DIFF_GATE_MODE=block python3 tools/diffgate.py check < CHANGES.diff   # exit 2 past a limit
python3 tools/diffgate.py check --max-files 10 --max-lines 800 --max-concerns 5 < CHANGES.diff
```

`DIFF_GATE_MAX_FILES`, `DIFF_GATE_MAX_LINES`, and
`DIFF_GATE_MAX_CONCERNS` set the same limits from the environment.
Flags win over env, env over the built-ins. Input with no diff
content passes open with a stderr note, so hooks never fail on
empty output.

## Hooks

- Claude Code: `hooks/hooks.json` ships in the plugin and gates the
  working tree after edits.
- Codex: root `hooks.json` ships in the plugin. Commands resolve from the plugin root.
- Antigravity: merge `hooks/antigravity-hooks.json` into the project's
  `.agents/hooks.json`, then fix the command path to your checkout.
- OpenCode: `plugin.js` exposes `checkDiff(diff, options)`. Call it from
  your session's post-edit step. Tool-event names stay out until a local
  config confirms them.
- Muse: no native hook ships yet; see `docs/muse-hooks-TBD.md`. The CLI works as-is.

## Requirements

- `tools/diffgate.py` is stdlib-only (Python 3.9+, no third-party packages).
- The OpenCode shim (`plugin.js`) needs node plus the `@opencode-ai/plugin`
  dependency from `package.json`, and shells out to `python3`.
