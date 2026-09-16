# Plan 006: Add native Muse hook wiring for all six gates

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- plugins/slop-gate/hooks.json plugins/slop-gate/hooks/hooks.json plugins/slop-gate/tools/slop.py tests/test_slop_manifests.py`
>Representative paths only — this plan touches all six gated plugins in
> the same pattern. If any of these changed since this plan was written,
> compare the "Current state" excerpts against the live code before
> proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: 001 (syntax gate should be watching before hook files multiply)
- **Category**: dx
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

The repo is consumed through Muse, yet all six gates ship
`docs/muse-hooks-TBD.md` ("no Muse hook manifest or event schema was
found ... lands once a Muse hook envelope can be copied from a real
local install instead of guessed"). Users get CLI-only usage under
Muse. This plan copies the real envelope, wires it, and deletes the TBD
notes.

## Current state

Facts (verified by reading the files):

- `plugins/slop-gate/hooks.json` (Claude envelope, plugin root):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ./tools/slop.py check --json"
          }
        ]
      }
    ]
  }
}
```
- `plugins/slop-gate/hooks/hooks.json` — second hooks file inside
  `hooks/` dir (per-plugin; exact content NOT read during planning —
  you must read it in Step 1 and reconcile which file is canonical for
  which runtime before adding a third).
- `plugins/slop-gate/docs/muse-hooks-TBD.md` (6 files, all DIFFERENT
  md5sums — each has per-plugin CLI commands; read each before deleting):
```markdown
# Muse native hooks: TBD

No local Muse hook manifest or event schema was found during the build
session, so this plugin ships no Muse hook wiring. The CLI still works
under Muse today:

- Run `python3 tools/slop.py score FILE` to check prose on demand.
- Run `python3 tools/slop.py check FILE` in scripts; set
  `SLOP_GATE_MODE=block` when a nonzero exit must fail the step.

Native hook support lands once a Muse hook envelope can be copied from
a real local install instead of guessed.
```
- `hook_file_from_stdin()` in `slop.py:649-668` already accepts the
  Claude PostToolUse envelope plus variants (`tool_input.file_path`,
  `toolCall.args`, `args`, `TargetFile`, `tool_response.filePath`).
  Other tools have equivalents — check each.
- Manifest tests to mirror: `tests/test_*_manifests.py` contain
  `test_claude_hooks_envelope` and `test_codex_hooks_envelope`. Read
  one pair fully in Step 1; new Muse tests must follow the same structure.
- Tests `test_muse_tbd_note_present` (seen in `test_verify_manifests.py`
  output) assert the TBD notes EXIST — they must be updated/removed as
  part of this plan.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Muse present? | `command -v muse` | path printed, or empty (see STOP conditions) |
| TBD notes | `ls plugins/*/docs/muse-hooks-TBD.md` | 6 files (0 after Step 4) |

## Scope

**In scope**:
- New per-plugin Muse hook manifest(s) — filename/location copied from the real Muse install, NOT invented.
- `plugins/*/tools/*.py` stdin-envelope parsing ONLY IF the Muse event differs from handled variants (minimal `or` branch, same style as existing).
- `tests/test_*_manifests.py` — replace `test_muse_tbd_note_present` with Muse envelope tests mirroring the Claude ones.
- Delete the six `docs/muse-hooks-TBD.md` files.

**Out of scope** (do NOT touch):
- `plugins/*/hooks.json`, `plugins/*/hooks/hooks.json`, `antigravity-hooks.json` — other runtimes frozen.
- Scoring/gating logic (thresholds, weights, bands) — envelope plumbing only.
- `plugins/core-tools/**` — no hooks there.
- Guessing a schema. If no real envelope is observable, STOP (below).

## Git workflow

- Branch: `advisor/006-muse-hooks`
- Commit style: conventional commits, e.g. `feat: add Muse native hooks for six gates` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Recon — read what planning did not

1. Read all six `plugins/*/hooks/hooks.json` fully; record which runtime each serves and how it differs from the root `hooks.json`.
2. Read `tests/test_slop_manifests.py` fully (or one full per-plugin file): copy the exact assertion style of `test_claude_hooks_envelope`, `test_codex_hooks_envelope`, and `test_muse_tbd_note_present`.
3. Run `command -v muse`. If present, hunt the real hook manifest path + event schema on disk (see Step 2).

**Verify**: you can state in your report (a) the role of `hooks/hooks.json` vs root `hooks.json`, (b) the TBD-test assertion text, (c) whether `muse` exists in this environment.

### Step 2: Capture the real Muse envelope

On a machine with Muse installed (this environment or one the operator gives you):
- Locate Muse's hook manifest + a sample hook event (config docs, `muse plugins validate` output, or an installed plugin's hook file — record the source path).
- Paste the sample event JSON into your report notes (NOT into the repo).

If `command -v muse` is empty AND the operator cannot point at a Muse install: STOP (condition below). Do not invent a schema.

**Verify**: sample Muse hook event JSON in hand, source path recorded.

### Step 3: Wire the six plugins

For each gated plugin (slop, ledger, diffgate, donecheck, reviewfmt, commitcheck):
1. Add the Muse manifest in the location/filename the real install uses, pointing at the existing `tools/*.py check` CLI (same command style as the Claude envelope, adjusted only for Muse's schema).
2. If the Muse event's file-path field is not among the variants the tool already parses, add one minimal branch in the same style. No other logic changes.
3. In `tests/test_<name>_manifests.py`: delete/replace `test_muse_tbd_note_present` with `test_muse_hooks_envelope` mirroring the Claude test's assertions against the new file.

**Verify**: `python3 tests/run.py` → 0 failed after all six.

### Step 4: Delete TBD notes, live-fire one gate

1. `git rm plugins/*/docs/muse-hooks-TBD.md` (6 files).
2. Live test with the REAL Muse event from Step 2 piped to one tool's stdin: `echo '<event>' | python3 plugins/slop-gate/tools/slop.py check --json` (adapt: use an event naming a real on-disk file, e.g. `tests/fixtures/slop/sloppy.md`) → expect the JSON `systemMessage` envelope on stdout.

**Verify**: `ls plugins/*/docs/muse-hooks-TBD.md` → "No such file". Live-fire prints `systemMessage` JSON. Full suite green.

## Test plan

- Replace 6 `test_muse_tbd_note_present` tests with 6 `test_muse_hooks_envelope` tests.
- Pattern: the sibling `test_claude_hooks_envelope` in each same file.
- Verification: `python3 tests/run.py` → all pass; plus the Step 4 live-fire.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] `ls plugins/*/docs/muse-hooks-TBD.md` fails (all 6 gone)
- [ ] `grep -rn "muse_tbd_note_present" tests/` returns no matches
- [ ] `grep -rln "test_muse_hooks_envelope" tests/` returns 6 files
- [ ] Live-fire from Step 4 prints `systemMessage` JSON
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- No Muse install / schema / sample event is observable anywhere — the TBD note's own precondition. Leave everything untouched and report "blocked: no Muse envelope source".
- `plugins/*/hooks/hooks.json` turns out to BE the Muse-intended file (naming collision) — report the actual layout instead of adding a duplicate.
- The Muse event schema requires tool changes beyond one parse branch (e.g. different exit codes) — report; that is a bigger plan.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- Future gates must ship Muse + Claude + Antigravity wiring together; update `add-plugin.sh`/`.ps1` templates in a follow-up (not here).
- Reviewer: scrutinize that no invented schema fields slipped in — every manifest key must trace to the Step 2 sample.
- After this lands, plan 007 can flip the Muse row in the install matrix.
