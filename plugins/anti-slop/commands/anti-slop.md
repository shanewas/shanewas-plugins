---
description: Audit text for AI slop, check grammatical tells, and suggest direct human rewrites
argument-hint: "[file] (optional path to check, or pass - for stdin)"
---

# Anti-Slop Command

1. Target file: use the argument if provided, or the most recently edited file.
2. Run `python3 skills/anti-slop/scripts/detect_slop.py FILE` to analyze score (0-100), grammatical tells, and voice deviations.
3. If score > 20 or deviations appear, apply suggestions or run `python3 skills/anti-slop/scripts/clean_slop.py FILE`.
