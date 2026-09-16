# Plan 005: Make Antigravity hook snippets installable without hand-editing

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- plugins/slop-gate/hooks/antigravity-hooks.json plugins/audit-trail/hooks/antigravity-hooks.json plugins/minimal-diff/hooks/antigravity-hooks.json plugins/verify-done/hooks/antigravity-hooks.json plugins/review-pair/hooks/antigravity-hooks.json plugins/commit-gate/hooks/antigravity-hooks.json`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

Every `hooks/antigravity-hooks.json` ships a literal
`/path/to/<name>/tools/*.py` placeholder with a `_note` saying "fix the
command path". Each installer hand-edits JSON. A copy-paste `sed`
one-liner in the note removes the guesswork while keeping the file a
static snippet (no installer to maintain).

## Current state

- `plugins/slop-gate/hooks/antigravity-hooks.json` (read in full):
```json
{
  "_note": "Merge this entry into your project's .agents/hooks.json. Fix the command path to point at your slop-gate checkout.",
  "slop-gate": {
    "SessionStart": null,
    "PreInvocation": null,
    "PostInvocation": null,
    "Stop": null,
    "PreToolUse": null,
    "PostToolUse": [
      {
        "matcher": "write_to_file|replace_file_content",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/slop-gate/tools/slop.py check --json",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```
- The other five files share this shape with their own plugin/tool names
  (confirm: `grep -h '"command"' plugins/*/hooks/antigravity-hooks.json`).
- Shape tests exist and MUST keep passing: `tests/test_slop_manifests.py`
  (and per-plugin siblings) contain `test_antigravity_snippet_shape`.
  Read one before editing — the top-level keys and nesting it asserts
  are frozen.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Snippet shape | `grep -h '"command"' plugins/*/hooks/antigravity-hooks.json` | 6 lines, one per plugin |
| JSON validity | `for f in plugins/*/hooks/antigravity-hooks.json; do python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" || echo "BAD $f"; done` | no output |

## Scope

**In scope** (the only files you should modify):
- The six `plugins/<name>/hooks/antigravity-hooks.json` files — `_note` value ONLY.

**Out of scope** (do NOT touch):
- Everything else in those JSON files (keys, matcher, command, timeout) — pinned by shape tests.
- `plugins/*/hooks/hooks.json` (Claude envelope) and `plugins/*/hooks.json` — different runtimes.
- Any installer script — deliberately not built; static snippet + one-liner only.

## Git workflow

- Branch: `advisor/005-antigravity-note`
- Commit style: conventional commits, e.g. `docs: add install one-liner to antigravity snippets` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Read the shape test

Open `tests/test_slop_manifests.py`, find
`test_antigravity_snippet_shape`, and note exactly which keys/structure
it asserts.

**Verify**: you can quote the asserted keys in your final report (e.g.
"_note + plugin key + PostToolUse list" — whatever it actually checks).

### Step 2: Rewrite the six _note values

New `_note` template (fill `<name>` per plugin, keep it one JSON string):

"Merge this entry into your project's .agents/hooks.json, replacing /path/to/<name> with your checkout. One-liner (run from the plugin dir): sed \"s#/path/to/<name>#$(pwd)#g\" hooks/antigravity-hooks.json > /tmp/<name>-hooks.json, then merge /tmp/<name>-hooks.json."

The `g` flag is load-bearing: `_note` holds two `/path/to/<name>`
occurrences on one line, so a non-global substitute leaves one behind
and Step 3's count never reaches 0 (learned in execution round 1).

Rules: valid JSON string escaping (the inner double quotes around the
sed expression must be `\"`); no other key touched.

**Verify**: the JSON-validity command from the table → no output (no BAD lines).
**Verify**: `grep -h "_note" plugins/*/hooks/antigravity-hooks.json` → 6 lines each containing `sed`.

### Step 3: Prove the one-liner works

Pick slop-gate, run its documented sed from the plugin dir, confirm the
output has no `/path/to` remnant and still parses as JSON.

**Verify**: `cd plugins/slop-gate && sed "s#/path/to/slop-gate#$(pwd)#g" hooks/antigravity-hooks.json > /tmp/slop-gate-hooks.json && grep -c "/path/to" /tmp/slop-gate-hooks.json` → `0`. Then `python3 -c "import json; json.load(open('/tmp/slop-gate-hooks.json'))"` → exit 0.
**Verify**: `python3 tests/run.py` → 0 failed.

## Test plan

- No new tests. Existing `test_*_antigravity_snippet_shape` tests guard the change.
- Verification: JSON-validity loop + sed proof + full suite.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] All 6 snippet files parse as JSON (validity loop silent)
- [ ] `grep -c /path/to plugins/*/hooks/antigravity-hooks.json` still shows the placeholder in `command` (snippet stays generic) while `_note` holds the sed recipe
- [ ] `git status` shows only the 6 in-scope files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `test_antigravity_snippet_shape` asserts the `_note` CONTENT (not just presence) — the plan's approach collides with the test; report.
- The six files' shapes differ from each other beyond plugin/tool names.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If Antigravity ever supports env/path expansion in hook commands, replace the sed recipe with the native mechanism.
- Reviewer: validate the sed one-liner on Windows Git Bash too if possible (repo has Windows users); POSIX `sed` + `$(pwd)` should hold.
