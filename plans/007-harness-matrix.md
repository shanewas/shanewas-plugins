# Plan 007: Verify each harness install path and flip the matrix

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- README.md docs/`
> If README.md changed since this plan was written, compare the
> "Current state" excerpts against the live file before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: 006 for the Muse row only (other four rows are independent; do those first if 006 is still open)
- **Category**: docs
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

README's install matrix marks all five harnesses TBD ("no live spike
verification evidence"). Users cannot tell which paths actually work.
One hands-on pass per harness, with pasted command output as evidence,
turns the matrix into a trust anchor.

## Current state

- `README.md` lines 7-48: install instructions for Claude Code, Muse
  Code, OpenCode, Antigravity, Hermes (read in full during planning —
  re-read the live file in Step 1, plans 002-004 may have touched nearby lines).
- `README.md` lines 74-87: the matrix, all five rows `TBD`:
```
| Harness | Install path (repo-observed) | Verified |
|---|---|---|
| Claude Code | `claude plugin marketplace add ...` ... | TBD |
| Muse Code | `muse plugins marketplace add ...` ... | TBD |
| OpenCode | Reference `plugins/core-tools/plugin.js` ... | TBD |
| Google Antigravity | Copy/mount `plugins/core-tools` ... | TBD |
| Hermes | Drop `plugins/<name>/skills/` folders ... | TBD |
```
- `muse plugins validate` exists as a check for the Muse row (see
  `.github/workflows/ci.yml`); other harnesses need their own "it loaded"
  signal, defined per-row in Step 2.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Matrix state | `grep -c "TBD" README.md` | 5 before, fewer after (0 if all verifiable) |

## Scope

**In scope** (the only files you should modify):
- `README.md` — install sections (only if a step proves wrong) + matrix `Verified` cells.
- `docs/harness-evidence.md` (create) — per-harness dated log: commands run, output pasted, version strings.

**Out of scope** (do NOT touch):
- `plugins/**`, `tests/**`, manifests — verification only; if a harness path is BROKEN, fix the docs to match reality (or mark the row `BROKEN: <reason>`), do not fix the plugin here.
- Any harness config on the operator's machine outside clearly-temp locations — ask before writing to `~/.config`, `~/.gemini`, etc.

## Git workflow

- Branch: `advisor/007-harness-matrix`
- Commit style: conventional commits, e.g. `docs: verify harness install matrix` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Re-read install docs, set up evidence log

Re-read README lines 1-87 live. Create `docs/harness-evidence.md` with
this skeleton:

```markdown
# Harness verification evidence

## <Harness> — <YYYY-MM-DD> — <operator env>
- Commands: ...
- Output: ...
- Result: VERIFIED | TBD (reason) | BROKEN (reason)
```

(one section per harness).

**Verify**: file exists with 5 empty sections.

### Step 2: Run one spike per harness

For EACH row, run the documented commands (use `core-tools` as the
probe plugin, matching the docs), record literal output in the evidence
log, and define "loaded" as:

- Claude Code: `claude plugin marketplace add ...` + install succeed, and the skill/command appears in the harness listing.
- Muse Code: `muse plugins marketplace add ...` + install succeed; `muse plugins validate plugins/core-tools` clean. (If plan 006 is done, also confirm the native hook fires; otherwise note hooks as follow-up.)
- OpenCode: `node --check plugins/core-tools/plugin.js` + the documented `opencode.json` reference loads without error in a real opencode run (or the closest load check opencode offers — record what you used).
- Antigravity: copy per docs into a TEMP dir (not the operator's real `~/.gemini` without asking), confirm `gemini-extension.json` discovery per Antigravity's docs.
- Hermes: copy a `skills/` folder per docs into a TEMP dir, confirm Hermes lists/loads it.

If a harness binary is absent in this environment: do NOT guess — record
`TBD (no <binary> in this environment)`, leave the matrix cell TBD, move on.

**Verify**: evidence log has all 5 sections filled with commands + pasted output + Result line each.

### Step 3: Flip the matrix

For each VERIFIED harness, replace its `TBD` with
`Yes (<YYYY-MM-DD>, <tool version>)`. For still-TBD rows append the
reason in the evidence log only (matrix cell stays `TBD`). If an install
step in lines 7-48 proves wrong, fix that step in the same edit.

**Verify**: `grep -c "TBD" README.md` equals the number of unverifiable harnesses (0 if all five passed). `python3 tests/run.py` → 0 failed.

## Test plan

- No new tests. Human-verified procedure with pasted evidence.
- Verification: evidence log completeness (5 Result lines) + suite green.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] `docs/harness-evidence.md` exists with 5 `## ` sections each containing a `Result:` line
- [ ] Every `Yes` cell in the matrix has a matching `Result: VERIFIED` section with pasted output
- [ ] No matrix cell claims `Yes` without evidence-log backup (spot-check by reviewer)
- [ ] `git status` shows only README.md + docs/harness-evidence.md
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Zero of five harnesses are installed in this environment — report "blocked: no harness binaries"; do not fabricate evidence.
- A documented install path fails AND the fix is unclear — mark the row `BROKEN: <symptom>` with evidence, continue with the other four, report.
- The operator forbids writing to the harness config dirs the spike needs — record TBD with reason, move on.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- Re-run spikes on major harness releases; the evidence log's date + version strings tell the next runner what is stale.
- Reviewer: the check is "could I reproduce this from the log?" — literal pasted output, not summaries.
- Partial completion is acceptable: each flipped row is independently valuable. Record unflipped rows as still-TODO in your report.
