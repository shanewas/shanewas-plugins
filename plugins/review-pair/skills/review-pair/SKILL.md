---
name: review-pair
description: Use when a code review needs a terse findings pass, when review findings must be validated as machine-readable pairs, or when review output should feed an audit ledger.
---

# Review Pair

Runs each review through two lenses: a terse findings pass, then an
audit-shape pass. The first lens reads the change and writes one
finding per line. The second lens runs `tools/reviewfmt.py` over
those lines and rejects anything a ledger cannot parse. It warns by
default and can block when `REVIEW_PAIR_MODE=block` is set. The tool
is one Python file with no third-party packages, so it runs anywhere
Python 3.9 does.

## First lens: terse findings

Read the change and write one finding per line. Lead with the worst:
blockers first, then majors, then minors, then nits. One line holds
one defect at one location. No greetings, no summaries, no
play-by-play of files you opened.

## Second lens: audit shape

Every line must match this shape:

```text
[RV-1] src/db.cs:12 blocker SQL string built from raw input here.
```

A bracketed `ID-number` tag, a `path:line` anchor, one of `blocker`,
`major`, `minor`, `nit`, then finding text of at least 10 characters.
A line missing any piece is malformed, not a finding.

## Commands

```bash
python3 tools/reviewfmt.py check FINDINGS.txt            # warn on blocker/major or malformed, exit 0
cat FINDINGS.txt | python3 tools/reviewfmt.py check      # read findings from stdin
python3 tools/reviewfmt.py check FINDINGS.txt --json     # machine-readable findings for a ledger
REVIEW_PAIR_MODE=block python3 tools/reviewfmt.py check FINDINGS.txt   # exit 2 when tripped
```

Missing, unreadable, or empty input fails open with a stderr note
and exit 0, so the gate never fails a session it cannot read.

## Hooks

- Claude Code: `hooks/hooks.json` ships in the plugin and checks
  findings piped on stdin after edits.
- Codex: root `hooks.json` ships in the plugin. Commands resolve from the plugin root.
- Antigravity: merge `hooks/antigravity-hooks.json` into the project's
  `.agents/hooks.json`, then fix the command path to your checkout.
- OpenCode: `plugin.js` exposes `checkReview(findings, options)`.
  Call it from your session's post-review step. Tool-event names stay
  out until a local config confirms them.
- Muse: no native hook ships yet; see `docs/muse-hooks-TBD.md`. The CLI works as-is.
