# Plan 003: Ship add-plugin.sh alongside add-plugin.ps1

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- add-plugin.ps1 README.md .github/workflows/ci.yml tests/run.py`
> If any in-scope-adjacent file changed since this plan was written, compare
> the "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (run after 001 so `bash -n` can join the syntax gate; if 001 is not done, add the step anyway and note the overlap)
- **Category**: dx
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

New plugins are scaffolded by `add-plugin.ps1`, which needs PowerShell.
Linux/macOS contributors — the majority for Claude Code harnesses — have
no native path. A small bash port using only bash + python3 (both already
required by the repo's tools) closes the gap.

## Current state

- `add-plugin.ps1` (106 lines, read in full during planning). Behavior:
  1. Params: `-Name` (required), `-Description` (default "Plugin description"), `-Category` (default "productivity").
  2. Refuses when `plugins/<Name>` exists (exit 1).
  3. Creates `.claude-plugin/`, `skills/<Name>/`, `commands/`, `agents/` dirs.
  4. Writes `.claude-plugin/plugin.json` (name/description/version 1.0.0/author Shanewas Ahmed), `gemini-extension.json` (+ contextFileName GEMINI.md), `package.json` (@shanewas/plugin-<Name>, MIT, main plugin.js, dep @opencode-ai/plugin ^1.17.8), stub `plugin.js`, stub `skills/<Name>/SKILL.md` with `---` frontmatter.
  5. Appends entry to root `.claude-plugin/marketplace.json` (source `./plugins/<Name>`, homepage `https://github.com/shanewas/shanewas-plugins`).
- Repo conventions: zero third-party deps; tests are stdlib-only functions
  named `test_*` in `tests/test_*.py`, auto-discovered by `tests/run.py`.
  Structural test pattern: `tests/test_slop_score.py` uses `subprocess.run`
  + fixtures under `tests/fixtures/`.
- CI file: `.github/workflows/ci.yml` (see plan 001 for full content; add a `bash -n` line to the syntax-gate step it creates — if plan 001 has not landed yet, add the whole syntax-gate step yourself including `bash -n add-plugin.sh`, and note this in your final report).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Shell syntax | `bash -n add-plugin.sh` | exit 0, no output |

## Scope

**In scope** (the only files you may create/modify):
- `add-plugin.sh` (create, executable bit set)
- `tests/test_add_plugin.py` (create)
- `tests/fixtures/add_plugin/marketplace.json` (create, minimal stub — see Step 2)
- `.github/workflows/ci.yml` (one line: `bash -n` in syntax-gate step)
- `README.md` (one bullet/line mentioning the .sh alternative next to the existing `add-plugin.ps1` references)

**Out of scope** (do NOT touch):
- `add-plugin.ps1` — frozen; the .sh must match its behavior, not change it.
- `.claude-plugin/marketplace.json` — the real catalog; tests use the fixture stub.
- Any `plugins/*` content.

## Git workflow

- Branch: `advisor/003-add-plugin-sh`
- Commit style: conventional commits, e.g. `feat: add bash plugin scaffolder` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Write add-plugin.sh

CLI: `add-plugin.sh --name NAME [--description TEXT] [--category CAT] [--root DIR]`.
`--root` defaults to the script's own directory (repo root in real use;
lets tests point at a temp dir).

Behavior (mirror the .ps1 exactly, including defaults and the
exists→exit-1 refusal):
- `mkdir -p` the four dirs.
- Write the four JSON files with python3 (one heredoc call) so quoting
  stays correct; field values identical to the .ps1 (author
  `Shanewas Ahmed <shanewasahmed@gmail.com>`, version `1.0.0`,
  homepage `https://github.com/shanewas/shanewas-plugins`).
- Write the stub `plugin.js` and stub `SKILL.md` with identical content
  to what the .ps1 generates (including the `---` frontmatter lines).
- Append the marketplace entry via python3 json round-trip.
- `chmod +x add-plugin.sh`. Note: the file must be committed with mode
  100755 — verify with `git ls-files -s add-plugin.sh`.

**Verify**: `bash -n add-plugin.sh` → exit 0. `git ls-files -s add-plugin.sh` → starts with `100755`.

### Step 2: Add fixture + tests

Fixture `tests/fixtures/add_plugin/marketplace.json`: minimal
`{"$schema": "...", "name": "test", "description": "t", "plugins": []}` —
just enough keys for the script's append step.

`tests/test_add_plugin.py` with at least these `test_*` functions
(pattern: `tests/test_slop_score.py` subprocess style; temp dirs via
stdlib `tempfile`/`shutil`):
1. `test_scaffold_creates_layout` — run script with `--root <tmp>`,
   assert the 4 dirs + 5 files exist and marketplace stub gained 1 entry.
2. `test_scaffold_refuses_existing` — run twice, second exits nonzero.
3. `test_scaffold_requires_name` — run without `--name`, exits nonzero.
4. `test_generated_json_parses` — every generated `*.json` loads with
   `json.load` and carries name/version/author.

**Verify**: `python3 tests/run.py` → all pass including the 4 new tests (grep the output for `test_add_plugin`).

### Step 3: Wire CI + README

- CI: add `bash -n add-plugin.sh` to the syntax-gate step (see Current
  state note if plan 001 has not landed).
- README: next to the `add-plugin.ps1` code block (lines 54-56) add one
  line: bash alternative
  `./add-plugin.sh --name "my-tool" --description "Repo linting and release checks"`.
  Also extend the layout bullet (line 69, or plan 002's version) to
  mention both scripts.

**Verify**: `grep -n "bash -n" .github/workflows/ci.yml` → 1+ matches.
**Verify**: `grep -n "add-plugin.sh" README.md` → 2+ matches.
**Verify**: full suite green.

## Test plan

- New file `tests/test_add_plugin.py`, 4 tests listed in Step 2.
- Pattern: `tests/test_slop_score.py` (subprocess + fixtures).
- Verification: `python3 tests/run.py` → all pass, output contains `ok test_add_plugin.test_scaffold_creates_layout` etc.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `bash -n add-plugin.sh` exits 0
- [ ] `git ls-files -s add-plugin.sh` shows mode 100755
- [ ] `python3 tests/run.py` exits 0; 4+ new `test_add_plugin.*` lines print `ok`
- [ ] `git status` shows only the 5 in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `add-plugin.ps1` behavior differs from the Current state summary (read it fully — 106 lines — before writing the port).
- `tests/run.py` discovery does not pick up the new test file.
- The real `.claude-plugin/marketplace.json` gets modified by a test run (tests must use the fixture stub only).
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- The .ps1 and .sh must evolve together. A reviewer should reject future changes to one without the other; a parity test (diff the two scaffolds) is a possible follow-up, deliberately not required here.
- If plan 001 had not landed and you created the syntax-gate step yourself, say so in the final report so the 001 executor does not duplicate it.
