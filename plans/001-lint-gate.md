# Plan 001: CI fails on Python syntax errors and JS syntax errors

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- .github/workflows/ci.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

CI currently runs only `python3 tests/run.py` plus an optional Muse
validate. A `tools/*.py` file with a syntax error is caught only if a test
imports it, and a broken `plugin.js` is never checked at all. Every later
plan touches these files, so a cheap syntax gate must land first.

## Current state

- `.github/workflows/ci.yml` — whole file (27 lines):
```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  foundation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.9"

      - name: Lint + fixture tests
        run: python3 tests/run.py

      - name: Validate plugin bundles (Muse)
        run: |
          if command -v muse >/dev/null 2>&1; then
            for d in plugins/*/; do
              muse plugins validate "$d"
            done
          else
            echo "muse CLI not installed; skipping validate"
          fi
```
- Repo convention: zero third-party dependencies. The existing Muse step
  shows the pattern for optional tooling: `command -v X` guard with an
  echo-skip fallback. Match it for node.
- Test command (verified): `python3 tests/run.py` → `138 passed, 0 failed (138 total)`.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | `138 passed, 0 failed (138 total)` (count may grow after other plans) |
| Py syntax | `python3 -m py_compile plugins/*/tools/*.py tests/*.py` | exit 0, no output |
| JS syntax | `for f in plugins/*/plugin.js; do node --check "$f"; done` | exit 0, no output |
| YAML check | `python3 -c "import yaml,sys" 2>/dev/null || echo NO-YAML` | informational only |

## Scope

**In scope** (the only files you should modify):
- `.github/workflows/ci.yml`

**Out of scope** (do NOT touch):
- `tests/run.py` and any `tests/test_*.py` — no test changes needed for a CI-only plan.
- Any third-party linter config (ruff/flake8/eslint) — repo is zero-dependency; stdlib `py_compile` and `node --check` only.
- `plugins/*/plugin.js` contents — if one fails `node --check`, STOP (see below), do not fix it here.

## Git workflow

- Branch: `advisor/001-lint-gate`
- Commit style: conventional commits, e.g. `ci: fail fast on py/js syntax errors` (repo's observed commit: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add syntax-gate step to ci.yml

Insert a new step AFTER `Set up Python` and BEFORE `Lint + fixture tests`:

```yaml
      - name: Syntax gate (py + js)
        run: |
          python3 -m py_compile plugins/*/tools/*.py tests/*.py
          if command -v node >/dev/null 2>&1; then
            for f in plugins/*/plugin.js; do
              node --check "$f"
            done
          else
            echo "node not installed; skipping node --check"
          fi
```

Keep the existing steps untouched and in order.

**Verify**: `cat .github/workflows/ci.yml` shows the new step in position 3 of 5 (after setup-python, before fixture tests).

### Step 2: Prove the gate passes locally

Run exactly what CI will run:

**Verify**: `python3 -m py_compile plugins/*/tools/*.py tests/*.py` → exit 0, no output.
**Verify**: `for f in plugins/*/plugin.js; do node --check "$f"; done` → exit 0 (if node exists; if not, record `node missing locally, CI check skipped` and continue).
**Verify**: `python3 tests/run.py` → `138 passed, 0 failed (138 total)`.

### Step 3: Prove the gate catches breakage

Temporarily append `def broken(:` to a COPY of one tool file in /tmp (never to the repo), run `python3 -m py_compile` on it, confirm nonzero exit, delete the copy.

**Verify**: py_compile on the broken copy exits nonzero with SyntaxError; `git status` shows only `.github/workflows/ci.yml` modified.

## Test plan

- No new tests. This plan adds a CI step, not repo code.
- Structural pattern: the existing `command -v muse` guard in the same file.
- Verification: the three commands in Step 2.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 -m py_compile plugins/*/tools/*.py tests/*.py` exits 0
- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] `grep -c "node --check" .github/workflows/ci.yml` returns 1 or more
- [ ] `grep -c "py_compile" .github/workflows/ci.yml` returns 1 or more
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The live `ci.yml` does not match the excerpt above.
- `node --check` fails on any existing `plugin.js` — that is a real bug for its own plan, not a drive-by fix here.
- `python3 tests/run.py` fails — the tree was already red; report, do not fix under this plan.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If a new interpreted language enters the repo (e.g. shell tools from plan 003), extend this step with its syntax check (`bash -n`).
- Reviewer: confirm the step ordering — syntax gate must stay BEFORE the test step so failures are fast and obvious.
- Deferred: real linting (unused imports, style). Deliberately out of scope; zero-dep ethos forbids ruff/flake8 vendoring without a maintainer decision.
