---
name: audit-trail
description: Use when AI-made edits need a visible audit trail, when reviewing what changed per file and turn, or when wiring edit logging into hooks.
---

# Audit Trail

Logs each edit to a local JSONL ledger straight from the hook event,
then renders the ledger as a review digest. One Python file, no
third-party packages, runs anywhere Python 3.9 does.

## Commands

```bash
<hook-event-JSON> | python3 tools/ledger.py append   # log one edit, always exit 0
python3 tools/ledger.py digest                       # per-file change list
python3 tools/ledger.py digest LEDGER --json         # machine-readable digest
```

`append` reads the hook event on stdin and appends one v1 record. Bad
input earns a stderr note and exit 0, so a broken event never fails
the hook. The ledger lives at `$AUDIT_TRAIL_LEDGER`, else
`.audit-trail/ledger.jsonl` under the working directory, created on
demand.

## Hooks

- Claude Code: `hooks/hooks.json` ships in the plugin and logs after edits.
- Codex: root `hooks.json` ships in the plugin. Commands resolve from the plugin root.
- Antigravity: merge `hooks/antigravity-hooks.json` into the project's
  `.agents/hooks.json`, then fix the command path to your checkout.
- OpenCode: `plugin.js` exposes `appendAudit(event)`. Call it from
  your session's post-edit step. Tool-event names stay out until a local
  config confirms them.
- Muse: no native hook ships yet; see `docs/muse-hooks-TBD.md`. The CLI works as-is.

## Record schema (v1)

Each ledger line carries: `schema`, `ts`, `session`, `turn`, `tool`,
`file`, `lines_added`, `lines_removed`, `claim_refs`. The event reader
accepts the Claude PostToolUse envelope plus flat variants carrying
`tool`/`file`/`session`/`turn` and an `edited_lines` payload with
`added`/`removed` counts.

## Digest

`digest` groups edits by file in first-seen order, with added/removed
line counts, edit counts, and turn refs. Corrupt lines are skipped
with a stderr note rather than failing the review.

## Requirements

- `tools/ledger.py` is stdlib-only (Python 3.9+, no third-party packages).
- The OpenCode shim (`plugin.js`) needs node plus the `@opencode-ai/plugin`
  dependency from `package.json`, and shells out to `python3`.
