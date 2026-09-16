# Plan 009: Make the diff-gate concern proxy count ideas, not coincidences

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- plugins/minimal-diff/tools/diffgate.py plugins/minimal-diff/skills/minimal-diff/SKILL.md tests/test_diff_gate.py tests/fixtures/diff/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: 001 (syntax gate watching before touching the gate)
- **Category**: tech-debt
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

`concerns_of()` returns distinct-top-level-dirs PLUS distinct-extensions.
A single-idea change touching `docs/a.md`, `docs/b.md`, `src/c.py`
scores 2 dirs + 2 exts = 4 concerns and trips the default max-3 — a
false trip on a focused change. The proxy should approximate "how many
ideas", and additive double-counting is the crudest option.

## Current state

Facts (`plugins/minimal-diff/tools/diffgate.py` read in full, 221 lines):

- `concerns_of()` lines 108-117:
```python
def concerns_of(paths):
    """Rough concern proxy: distinct top-level dirs plus extensions."""
    dirs = set()
    exts = set()
    for path in paths:
        parts = path.split("/")
        dirs.add(parts[0] if len(parts) > 1 else "(root)")
        base = parts[-1]
        exts.add(base.rsplit(".", 1)[1].lower() if "." in base else "(none)")
    return len(dirs) + len(exts)
```
- Defaults lines 42-44: `DEFAULT_MAX_FILES = 5`, `DEFAULT_MAX_LINES =
  400`, `DEFAULT_MAX_CONCERNS = 3`. Threshold plumbing
  (`resolve_threshold`, flags, `DIFF_GATE_MAX_*` env) lines 120-131 —
  frozen, do not touch.
- Docstring lines 11-14 describe the proxy; SKILL.md `## Limits`
  section documents the same. Both must be updated together with code.
- Fixtures: `tests/fixtures/diff/` holds `small.diff`, `large.diff`,
  `concerns.diff`, `garbage.txt` (NOT read during planning — you must
  read all four plus `tests/test_diff_gate.py` in full in Step 1; the
  tests pin current proxy outputs and you need to know exactly what
  will change).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Gate probe | `python3 plugins/minimal-diff/tools/diffgate.py check tests/fixtures/diff/concerns.diff` | current output (record before changing) |

## Scope

**In scope**:
- `concerns_of()` body + its docstring line in `diffgate.py` (function only — lines 108-117 region).
- Module docstring proxy sentence (lines 11-14) to match.
- `plugins/minimal-diff/skills/minimal-diff/SKILL.md` `## Limits` section to match.
- `tests/test_diff_gate.py` updates + `tests/fixtures/diff/` additions for the new proxy.

**Out of scope** (do NOT touch):
- `parse_diff`, `resolve_threshold`, `warn_line`, `cmd_check`, arg parser, defaults, exit codes — proxy math only.
- Any other plugin's tools.
- Existing fixture FILES — read-only oracles; if the new proxy changes their expected outputs, update the TEST EXPECTATIONS (with justification in your report), never the fixture bytes.

## Git workflow

- Branch: `advisor/009-concern-proxy`
- Commit style: conventional commits, e.g. `fix: count diff concerns without double-count` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Read the pinned behavior

1. Read `tests/test_diff_gate.py` in full + all four files in `tests/fixtures/diff/`.
2. Record: for each fixture, current `concerns_of()` output and which test asserts it.
3. Run the gate probe on each fixture, save outputs.

**Verify**: your report lists per-fixture current concern counts and the asserting test names.

### Step 2: Pick and implement the new proxy

Candidate (adopt unless Step 1 evidence argues otherwise):
`max(len(dirs), len(exts))` — a change stays one concern when either
dimension is one; genuinely scattered changes still trip. Single-idea
multi-type edits (`docs/*.md` + `src/*.py`) score 2, not 4.

Rules:
- Keep it a pure function of `paths`, same signature, stdlib-only.
- Keep `(root)`/`(none)` sentinels behavior (or justify removal).
- Update the function docstring + module docstring + SKILL.md `## Limits` to state the formula EXACTLY (executor's words must match code).

**Verify**: `python3 -c` one-liner importing diffgate and printing
`concerns_of()` for `["docs/a.md","docs/b.md","src/c.py"]` → `2` (if candidate adopted).

### Step 3: Update tests + fixtures

1. Update existing expectations that the new proxy changes — each change
   needs a one-line justification comment citing the new formula.
2. Add fixture `tests/fixtures/diff/mixed-single-idea.diff` (one idea,
   two dirs, two exts — must NOT trip concerns) + test
   `test_single_idea_mixed_types_passes` following the file's existing pattern.
3. Keep a trip-case covered: existing `concerns.diff` test (or a new
   fixture) must still trip on concerns — a proxy no test can trip is
   dead code.

**Verify**: `python3 tests/run.py` → 0 failed; output contains `ok` for the new test.

## Test plan

- Update `tests/test_diff_gate.py` expectations per Step 3 + one new
  fixture + one new test.
- Pattern: the same file's existing tests (read in Step 1).
- Verification: full suite green + new-test `ok` line.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] New test `test_single_idea_mixed_types_passes` (or honestly-named equivalent) exists and passes
- [ ] At least one test still asserts a concerns-trip (no dead proxy)
- [ ] `git diff --stat` shows only the 4 in-scope paths
- [ ] Docstring + SKILL.md state the same formula as the code (reviewer spot-check)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Step 1 shows tests asserting proxy outputs you cannot reproduce (tree already drifted — report).
- No new-proxy candidate keeps a meaningful trip-case without also rewriting fixtures (fixtures are frozen; report and stop).
- The change wants to touch thresholds, defaults, or exit codes — out of scope; report.
- The live `concerns_of` does not match the Current state excerpt.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- The proxy is heuristic by nature; if it trips wrongly again, the next
  step is per-repo calibration (env defaults), not more clever math.
- Reviewer: check each updated test expectation carries its justification comment, and that the trip-case is realistic (not constructed to pass).
