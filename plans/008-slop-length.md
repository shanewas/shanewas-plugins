# Plan 008: Measure slop-gate length bias, then document or fix

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 3c53bae..HEAD -- plugins/slop-gate/tools/slop.py plugins/slop-gate/skills/slop-gate/SKILL.md tests/test_slop_score.py tests/fixtures/slop/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: 001 (syntax gate watching before touching the scorer)
- **Category**: tech-debt
- **Planned at**: commit `3c53bae`, 2026-09-16

## Why this matters

`slop.py` scoring is flat-additive with no length normalization (stated
as deliberate in the docstring: "a small edit carrying strong slop
signals still trips the gate"). The flip side is unmeasured: long clean
documents accumulate incidental hits and may trip the 20 threshold on
noise. This plan measures the bias on real long-clean text first, then
either documents the limitation or implements a bounded fix. Measurement
before code — the current behavior may be fine.

## Current state

Facts (slop.py read in full, 778 lines):

- `_calculate_score()` (lines 586-596): sums `len(findings[cat]) *
  weight` per category (weights: high_risk 10, thesaurus 8,
  japanese_slop 10, meta_commentary 8, medium_risk 5, buzzwords 5,
  hedging 4, structure 10) plus rhythm deviations capped at
  `RHYTHM_CAP = 30`, total capped at 100. No division by length
  anywhere; rhythm metrics themselves ARE length-normalized
  (per_100w etc.) but phrase hits are raw counts.
- Bands: `band_for_score()` lines 250-258: <20 clean, <40 marginal,
  <60 heavy, else severe. Boundary fixtures (`tests/fixtures/slop/
  boundary-20.md` etc.) carry exact hit counts so scores equal exactly
  20/40/60 — `tests/test_slop_score.py::test_fixture_scores_exact_*`
  pin this. ANY scoring change must keep those tests green.
- `strip_markup()` (272-281) already removes code/tables/headings, so
  measurement corpus should be prose-heavy to be fair.
- SKILL.md documents bands + `SLOP_GATE_MODE=block`; threshold flag
  `--threshold` exists on `check`.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Tests | `python3 tests/run.py` | all pass, 0 failed |
| Score probe | `python3 plugins/slop-gate/tools/slop.py score FILE --json --no-profile` | JSON with score/band |

## Scope

**In scope**:
- Measurement corpus notes (transient, /tmp only — NOT committed).
- IF bias confirmed AND fix chosen: `plugins/slop-gate/tools/slop.py` scoring only, `tests/test_slop_score.py` + `tests/fixtures/slop/` additions, SKILL.md band/threshold docs.
- IF bias negligible: SKILL.md `## Known limits` paragraph only.

**Out of scope** (do NOT touch):
- Phrase lists, weights, rhythm metrics, profile/learn path — the fix (if any) is a length term only.
- Other plugins' tools.
- Boundary fixture FILES (`boundary-*.md`) — pinned oracles; read-only. (You may ADD fixtures.)

## Git workflow

- Branch: `advisor/008-slop-length`
- Commit style: conventional commits, e.g. `docs: document slop-gate length behavior` or `fix: bound slop phrase hits per word window` (observed: `3c53bae feat: add v1 audit-pack plugin set`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Measure (no code changes)

1. Assemble 5+ long CLEAN prose samples (800+ words each) in /tmp:
   human-written project docs are ideal (this repo's CHANGELOG.md,
   SECURITY.md, CONTRIBUTING.md + 2 of your own choosing — record
   choices). No AI-generated text in the corpus.
2. Score each: `python3 plugins/slop-gate/tools/slop.py score F --json --no-profile`, record score + band + hit counts.
3. Also score the existing `tests/fixtures/slop/clean.md` and `sloppy.md`
   as calibration anchors.

**Verify**: a table in your report: file, words, score, band, top hit categories. Decision rule: if 2+ clean samples score >= 20 → bias confirmed, go to Step 2b. Else → Step 2a.

### Step 2a: Bias negligible — document only

Append to SKILL.md:

```markdown
## Known limits

Scores are flat-additive with no length normalization: a long document
accumulates more incidental hits than a short one. Measured <DATE> on
<N> human-written samples of 800+ words, max clean score was <S>. If
long files trip the gate on noise, raise `--threshold` for that path
instead of editing the prose.
```

Fill `<DATE>`, `<N>`, `<S>` with real Step 1 numbers. Skip to Step 3.

**Verify**: `grep -c "Known limits" plugins/slop-gate/skills/slop-gate/SKILL.md` → 1.

### Step 2b: Bias confirmed — bounded fix

Constraints (ALL mandatory):
1. Boundary fixtures MUST still score exactly 20/40/60. Check their
   word counts first (`wc -w tests/fixtures/slop/boundary-*.md`) — if
   they are short (<300 words), any fix MUST be length-gated so short
   texts are untouched (e.g. apply only above 500 words).
2. Smallest possible change. Suggested shape (adapt if measurement
   says otherwise): cap total phrase-hit points per 500-word window,
   or scale phrase subtotal by `min(1, 500/words)` for texts over 500
   words. Rhythm path untouched.
3. Update the docstring's "no length normalization" sentence to describe
   the new behavior precisely.
4. Add fixtures: `tests/fixtures/slop/long-clean.md` (800+ human words,
   must score < 20) + test `test_long_clean_stays_clean` in
   `tests/test_slop_score.py` following the existing `_score_json` pattern.

**Verify**: `python3 tests/run.py` → 0 failed INCLUDING the pre-existing `test_fixture_scores_exact_*` tests (name them in your report as still passing).

### Step 3: Full suite + report

**Verify**: `python3 tests/run.py` → 0 failed. Report states which branch (2a/2b) was taken with the Step 1 table.

## Test plan

- Branch 2a: no new tests.
- Branch 2b: one new fixture + `test_long_clean_stays_clean`; regression
  guarded by existing `test_fixture_scores_exact_*` + `test_band_boundaries_exact`.
- Pattern: `tests/test_slop_score.py::_score_json`.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 tests/run.py` exits 0 with 0 failed
- [ ] Pre-existing `test_fixture_scores_exact_*` and `test_band_boundaries_exact` still pass (grep output for `ok`)
- [ ] Branch 2a: SKILL.md contains `## Known limits` with real numbers; `git status` shows only SKILL.md
- [ ] Branch 2b: new fixture + new test exist and pass; docstring updated; no other tool files touched
- [ ] `plans/README.md` status row updated (note which branch was taken)

## STOP conditions

Stop and report back (do not improvise) if:

- Step 1 corpus cannot reach 5 clean 800+ word samples of certain human provenance — report partial measurement, take branch 2a with what you have, flag the shortfall.
- Branch 2b breaks ANY `test_fixture_scores_exact_*` test — revert the scoring change, fall back to 2a, report.
- The fix wants to touch weights, phrase lists, or rhythm code — out of scope; report instead.
- The live `_calculate_score` does not match the Current state excerpt.
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If 2b landed: future weight/phrase changes must re-run the long-clean fixture; note this next to the new test.
- If 2a landed: the `## Known limits` numbers go stale as phrase lists evolve — refresh when lists change.
- Reviewer: verify the corpus was genuinely human-written (Step 1 file list); a synthetic corpus invalidates the measurement.
