# Plan 004: Scope the "zero-dependency" claim to tools/*.py

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- README.md plugins/slop-gate/skills/slop-gate/SKILL.md plugins/audit-trail/skills/audit-trail/SKILL.md plugins/minimal-diff/skills/minimal-diff/SKILL.md plugins/verify-done/skills/verify-done/SKILL.md plugins/review-pair/skills/review-pair/SKILL.md plugins/commit-gate/skills/commit-gate/SKILL.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

Every gate advertises "zero-dependency", but each `package.json`
declares `"@opencode-ai/plugin": "^1.17.8"` and each `plugin.js` shells
out to `python3` via `execFileSync`. The claim is true only for
`tools/*.py` (stdlib-only). Unscoped wording misleads installers about
what runs where. Docs-only fix: scope the claim, add a requirements note.

## Current state

Facts (all verified by reading the files):

- `plugins/slop-gate/package.json`:
```json
{
  "name": "@shanewas/plugin-slop-gate",
  "version": "1.0.0",
  "description": "Zero-dependency AI-slop scorer and edit gate for OpenCode, Claude Code, and Antigravity",
  "main": "plugin.js",
  "dependencies": {
    "@opencode-ai/plugin": "^1.17.8"
  }
}
```
  (Other five gated plugins follow the same shape; confirm with
  `grep -l opencode-ai plugins/*/package.json` — expect 6 matches,
  core-tools excluded.)
- `plugins/slop-gate/plugin.js` lines 1-20: imports `node:child_process`,
  resolves `tools/slop.py`, calls `execFileSync("python3", ...)` inside
  `checkSlop()`. Same pattern in the other five shims (function names:
  appendAudit, checkCommit, checkDiff, checkDone, reviewfmt wrapper —
  confirm each with `grep -n execFileSync plugins/*/plugin.js`).
- Each `tools/*.py` docstring states "stdlib only" / "no third-party
  packages" / "Python 3.9+" — that part is accurate and stays.
- Each gated `SKILL.md` opens with a sentence like "The tool is one
  Python file with no third-party packages, so it runs anywhere Python
  3.9 does." (slop-gate SKILL.md lines 8-10; others equivalent.)
- Frontmatter lint: `tests/test_skill_frontmatter.py` lints every
  SKILL.md — keep frontmatter blocks untouched.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Dep check | `grep -l opencode-ai plugins/*/package.json` | 6 lines (all but core-tools) |
| Shim check | `grep -ln execFileSync plugins/*/plugin.js` | 6 lines (all but core-tools) |

## Scope

**In scope** (the only files you should modify):
- The six gated `plugins/<name>/skills/<name>/SKILL.md` files (slop-gate, audit-trail, minimal-diff, verify-done, review-pair, commit-gate) — append a short `## Requirements` note to each.
- `README.md` — one sentence in `## Creating a Plugin` scoping the claim.

**Out of scope** (do NOT touch):
- `package.json`, `plugin.js`, `tools/*.py` — behavior and manifests frozen; wording fix only.
- SKILL.md frontmatter blocks (`---` headers) — the frontmatter lint test pins their shape.
- `plugins/core-tools/**` — no zero-dependency claim there (verify with grep; if one exists, STOP and report).

## Git workflow

- Branch: `advisor/004-zero-dep-scope`
- Commit style: conventional commits, e.g. `docs: scope zero-dependency claim to tools` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Confirm the claim surface

**Verify**: `grep -rln "zero-dependency\|no third-party" plugins/*/skills/ README.md` → list every hit; expect the 6 SKILL.md files (+ maybe README). If `core-tools` appears, STOP.
**Verify**: the two Commands-table greps return the expected 6 lines each.

### Step 2: Append Requirements notes

Append to EACH of the six SKILL.md files (at the end, same wording
except the tool path):

```markdown
## Requirements

- `tools/<tool>.py` is stdlib-only (Python 3.9+, no third-party packages).
- The OpenCode shim (`plugin.js`) needs node plus the `@opencode-ai/plugin`
  dependency from `package.json`, and shells out to `python3`.
```

Tool filenames: slop.py, ledger.py, diffgate.py, donecheck.py,
reviewfmt.py, commitcheck.py — confirm each exists before writing its note.

**Verify**: `grep -c "stdlib-only" plugins/*/skills/*/SKILL.md` → 1 for each of the 6 gated skills.

### Step 3: Scope the README sentence

In `## Creating a Plugin`, after the "Each package folder contains" list,
add: "The `tools/*.py` CLIs are stdlib-only; the node shims (`plugin.js`)
require node, `python3`, and the `package.json` dependencies."

**Verify**: `python3 tests/run.py` → 0 failed (frontmatter lint must stay green).

## Test plan

- No new tests. Docs-only change guarded by existing
  `tests/test_skill_frontmatter.py` (must stay green — proves frontmatter untouched).
- Verification: the grep counts in Steps 2-3 plus the full suite.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] `grep -c "stdlib-only" plugins/*/skills/*/SKILL.md` shows 1 for exactly the 6 gated skills, 0 for core-tools/git-summary
- [ ] `grep -c "stdlib-only" README.md` returns 1+
- [ ] `git status` shows only the 7 in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `core-tools` contains a zero-dependency claim (assumption "6 files" false).
- Any `package.json` lacks the `@opencode-ai/plugin` dep (claim surface differs from Current state).
- `tests/test_skill_frontmatter.py` fails after your edit (you touched frontmatter — revert and redo).
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If a gate ever gains a real third-party Python dep, its Requirements note and the README sentence must be updated in the same PR.
- Reviewer: check the six notes are identical apart from the tool filename.
