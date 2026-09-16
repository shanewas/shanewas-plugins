---
description: Check the current change against the minimal-diff size limits
argument-hint: "[diff] (optional path to a saved diff file)"
---

# Diff Command

1. Pick the diff: use the argument when given, else `git diff HEAD --`.
2. Run `python3 <plugin-root>/tools/diffgate.py check [DIFF]` and read the counts.
3. When the gate trips, split the change before you ask for review.
