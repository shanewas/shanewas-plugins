# Plan 002: README Repository Layout lists all seven plugins

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- README.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

README.md lines 65-69 describe the repo layout but name only
`core-tools`, although six more plugins shipped in v1.0.0. A new
contributor reading the README gets a wrong map of the repo. One-line-per-plugin
fix, zero behavior change.

## Current state

- `README.md` lines 65-69:
```markdown
## Repository Layout

- `.claude-plugin/marketplace.json`: Root catalog listing available packages
- `plugins/core-tools/`: Starter package with `git-summary` skill, `/summary` command, and audit agent
- `add-plugin.ps1`: PowerShell generator for new packages
```
- Ground truth for plugin list + one-line descriptions:
  `.claude-plugin/marketplace.json` (7 entries: core-tools, slop-gate,
  audit-trail, minimal-diff, verify-done, review-pair, commit-gate).
  Copy each `description` value verbatim from that file — it is the
  canonical wording.
- Other plugin dirs on disk (confirm with `ls plugins/`):
  audit-trail, commit-gate, core-tools, minimal-diff, review-pair,
  slop-gate, verify-done.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | `138 passed, 0 failed (138 total)` (count may grow after other plans) |
| Layout check | `ls plugins/` | 7 directories listed above |

## Scope

**In scope** (the only files you should modify):
- `README.md` — the `## Repository Layout` section only (lines 65-69).

**Out of scope** (do NOT touch):
- `## Installation`, `## Install Matrix` — covered by plan 007.
- `.claude-plugin/marketplace.json` — canonical source, read-only here.
- `add-plugin.ps1` mention stays as-is (plan 003 adds the .sh sibling and updates that bullet itself).

## Git workflow

- Branch: `advisor/002-readme-layout`
- Commit style: conventional commits, e.g. `docs: list all plugins in repo layout` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Rewrite the Repository Layout section

Replace lines 65-69 with:

```markdown
## Repository Layout

- `.claude-plugin/marketplace.json`: Root catalog listing available packages
- `plugins/audit-trail/`: <description from marketplace.json>
- `plugins/commit-gate/`: <description from marketplace.json>
- `plugins/core-tools/`: Starter package with `git-summary` skill, `/summary` command, and audit agent
- `plugins/minimal-diff/`: <description from marketplace.json>
- `plugins/review-pair/`: <description from marketplace.json>
- `plugins/slop-gate/`: <description from marketplace.json>
- `plugins/verify-done/`: <description from marketplace.json>
- `tests/`: Zero-dependency fixture tests, run with `python3 tests/run.py`
- `add-plugin.ps1`: PowerShell generator for new packages
```

Rules: alphabetical plugin order; descriptions copied verbatim from
marketplace.json; keep the existing core-tools wording (it is more
specific than the catalog entry).

**Verify**: `sed -n '65,80p' README.md` shows 7 plugin bullets between the heading and the tests bullet.

### Step 2: Cross-check names against disk and catalog

**Verify**: `for p in audit-trail commit-gate core-tools minimal-diff review-pair slop-gate verify-done; do grep -q "plugins/$p/" README.md || echo "MISSING $p"; done` → no output (no MISSING lines).
**Verify**: `python3 tests/run.py` → 0 failed (docs-only change, must stay green).

## Test plan

- No new tests. Docs-only change.
- Verification: the grep loop in Step 2 (every on-disk plugin appears in the layout section) plus the full suite staying green.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] Each of the 7 `plugins/<name>/` paths appears in README.md
- [ ] `git diff --stat` shows only README.md modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The live layout section does not match the excerpt above.
- `ls plugins/` shows a plugin NOT in marketplace.json (or vice versa) — catalog/disk skew is a bigger finding; report it.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If a new plugin is added later, its author must extend this list; consider asking plan 003's `add-plugin.sh` to print a reminder (not this plan's job).
- Reviewer: check descriptions match marketplace.json verbatim.
