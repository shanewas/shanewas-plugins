---
name: commit-gate
description: Use when a commit message needs a format check, when staged files must be screened for banned types, or when a commit should be gated on message shape and trailers.
---

# Commit Gate

Gates each commit on message shape and staged files. It checks the
subject against Conventional Commits (`type[(scope)][!]: description`,
50 chars max), body lines against 72 chars, trailers against AI
authorship, and staged paths against banned extensions. It warns by
default and can block when `COMMIT_GATE_MODE=block` is set. The tool is
one Python file with no third-party packages, so it runs anywhere
Python 3.9 does.

## Commands

```bash
python3 tools/commitcheck.py check --message-file MSG
python3 tools/commitcheck.py check --message-file MSG --staged "a.py\nb.md"
python3 tools/commitcheck.py check --message-file MSG --staged @list.txt --json
COMMIT_GATE_MODE=block python3 tools/commitcheck.py check --message-file MSG
```

With no `--staged` the tool runs `git diff --cached --name-only`
itself. `--staged` is repeatable; prefix a value with `@` to read the
newline-separated list from a file instead. Missing inputs and an
unavailable git fail open: stderr note, exit 0.

## Banned extensions

`.docx` and `.xlsx` ship banned; `.md` and `.json` stay allowed since
many repos commit them on purpose. Extend with `--ban md` or
`COMMIT_GATE_BAN`, waive with `--allow xlsx` or `COMMIT_GATE_ALLOW`.
Allow wins over ban.

## Ticket refs

Off by default. Pass `--ticket-regex 'PROJ-\d+'` to require a match
somewhere in the message.

## Git hook

No harness ships a commit-message event, so the sharpest wiring is a
plain git hook. Save as `.git/hooks/commit-msg` and make it executable:

```bash
#!/bin/sh
python3 /path/to/commit-gate/tools/commitcheck.py check \
  --message-file "$1"
```

Set `COMMIT_GATE_MODE=block` in your shell to turn warnings into
rejections.

## Hooks

- Claude Code: `hooks/hooks.json` ships in the plugin and fires after edits.
- Codex: root `hooks.json` ships in the plugin. Commands resolve from the plugin root.
- Antigravity: merge `hooks/antigravity-hooks.json` into the project's
  `.agents/hooks.json`, then fix the command path to your checkout.
- OpenCode: `plugin.js` exposes `checkCommit(messageFile, staged, options)`.
  Call it from your session's post-edit step. Tool-event names stay out
  until a local config confirms them.
- Muse: no native hook ships yet; see `docs/muse-hooks-TBD.md`. The CLI works as-is.

## Requirements

- `tools/commitcheck.py` is stdlib-only (Python 3.9+, no third-party packages).
- The OpenCode shim (`plugin.js`) needs node plus the `@opencode-ai/plugin`
  dependency from `package.json`, and shells out to `python3`.
