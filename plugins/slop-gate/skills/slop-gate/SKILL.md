---
name: slop-gate
description: Use when AI-written prose or code needs a slop check, when edits should be gated on slop score, or when calibrating a slop profile from samples.
---

# Slop Gate

Scores each edit for AI slop on a 0-100 scale. It warns by default and
can block when `SLOP_GATE_MODE=block` is set. The tool is one Python
file with no third-party packages, so it runs anywhere Python 3.9 does.

## Bands

- Under 20 is clean. Ship it.
- 20-40 is marginal. Give the text one quick pass.
- 40-60 is heavy. Revise before you share it.
- Over 60 is severe. Start over.

## Commands

```bash
python3 tools/slop.py score FILE            # report score plus band
python3 tools/slop.py score FILE --json     # machine-readable report
python3 tools/slop.py check FILE            # warn past threshold 20, exit 0
SLOP_GATE_MODE=block python3 tools/slop.py check FILE   # exit 2 past threshold
python3 tools/slop.py learn s1.md s2.md     # build voice profile
```

`check` with no file reads a hook event from stdin and scores the edited
file named there. It stays quiet when the score sits below the bar, so
hooks don't nag on clean edits.

## Hooks

- Claude Code: `hooks/hooks.json` ships in the plugin and fires after edits.
- Codex: root `hooks.json` ships in the plugin. Commands resolve from the plugin root.
- Antigravity: merge `hooks/antigravity-hooks.json` into the project's
  `.agents/hooks.json`, then fix the command path to your checkout.
- OpenCode: `plugin.js` exposes `checkSlop(file, threshold)`. Call it from
  your session's post-edit step. Tool-event names stay out until a local
  config confirms them.
- Muse: no native hook ships yet; see `docs/muse-hooks-TBD.md`. The CLI works as-is.

## Voice profiles

`learn` reads prose you wrote and writes `~/.slop-gate/voice-profile.json`.
Later runs judge rhythm against your own habits instead of fixed limits.
Point `--profile` at the file when it lives elsewhere. Pass
`--no-profile` to use the built-in limits.

## Scoring notes

Each hit adds fixed points: stock phrases 10, humanizer tells and
meta-commentary 8, filler and jargon 5, hedging 4. Rhythm checks add up
to 30 on prose with four or more sentences. Short notes and code files
skip them. Scores cap at 100.

## Requirements

- `tools/slop.py` is stdlib-only (Python 3.9+, no third-party packages).
- The OpenCode shim (`plugin.js`) needs node plus the `@opencode-ai/plugin`
  dependency from `package.json`, and shells out to `python3`.
