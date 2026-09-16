---
description: Check a done claim against required build, test, and artifact evidence
argument-hint: "[claim] (path to the done-claim file)"
---

# Done Command

1. Pick the claim: use the argument when given, else `$VERIFY_DONE_CLAIM`.
2. Run `python3 <plugin-root>/tools/donecheck.py check --claim CLAIM [--evidence LOG]` and read the verdict.
3. When the gate warns, cite the missing kinds or waive one with an `N/A:` reason before you declare done.
