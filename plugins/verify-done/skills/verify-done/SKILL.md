---
name: verify-done
description: Use when a done claim needs an evidence check, when work is declared complete without cited proof, or when a final report must reference build, test, and artifact evidence.
---

# Verify Done

Gates each done claim on cited evidence: build output, test output,
and an artifact or grep anchor. It warns by default and can block when
`VERIFY_DONE_MODE=block` is set. The tool is one Python file with no
third-party packages, so it runs anywhere Python 3.9 does.

## Evidence kinds

- Build output: the claim names the build (`build`).
- Test output: the claim names the run (`test`, `pass`, `green`).
- Artifact or anchor: the claim points at proof (`artifact`, `anchor`,
  `ledger`, `screenshot`).

Matching is case-insensitive. A kind the change honestly needs can be
waived with an `N/A:` line carrying a reason:

N/A: tests - typo-only change, no code paths touched.

A bare `N/A:` with no reason waives nothing.

## Commands

```bash
python3 tools/donecheck.py check --claim CLAIM.md                # warn on missing kinds, exit 0
python3 tools/donecheck.py check --claim CLAIM.md --evidence LOG # claim plus files/commands log
python3 tools/donecheck.py check --claim CLAIM.md --json         # machine-readable verdict
VERIFY_DONE_MODE=block python3 tools/donecheck.py check --claim CLAIM.md   # exit 2 on missing kinds
```

`--claim` and `--evidence` also resolve from `VERIFY_DONE_CLAIM` and
`VERIFY_DONE_EVIDENCE`. Missing or unreadable inputs fail open with a
stderr note and exit 0, so the gate never fails a session it cannot read.

## Hooks

- Claude Code: `hooks/hooks.json` ships in the plugin and checks the
  configured claim after edits.
- Codex: root `hooks.json` ships in the plugin. Commands resolve from the plugin root.
- Antigravity: merge `hooks/antigravity-hooks.json` into the project's
  `.agents/hooks.json`, then fix the command path to your checkout.
- OpenCode: `plugin.js` exposes `checkDone(claim, evidence, options)`.
  Call it from your session's post-edit step. Tool-event names stay out
  until a local config confirms them.
- Muse: no native hook ships yet; see `docs/muse-hooks-TBD.md`. The CLI works as-is.
