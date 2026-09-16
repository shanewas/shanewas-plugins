---
description: Check a commit message and staged files against the commit gate
argument-hint: "[message-file] (path to the commit message file)"
---

# Commit Command

1. Pick the message: use the argument when given, else ask for the message file.
2. Run `python3 <plugin-root>/tools/commitcheck.py check --message-file MSG` and read the verdict.
3. When the gate warns, fix the subject shape, trim long lines, drop AI trailers, or unstage banned files before you commit.
