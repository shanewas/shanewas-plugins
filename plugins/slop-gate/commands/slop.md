---
description: Score the current edit for AI slop and report the band
argument-hint: "[file] (optional path to check)"
---

# Slop Command

1. Pick the file: use the argument when given, else the file from your last edit.
2. Run `python3 <plugin-root>/tools/slop.py score FILE` and read the score plus band.
3. When the score tops 20, quote the worst hits and cut them before you ship.
