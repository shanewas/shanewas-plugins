---
description: Run the two-lens review pair and validate the findings shape
argument-hint: "[findings] (path to the findings file)"
---

# Review Command

1. First lens: read the change and write one terse finding per line, worst first.
2. Second lens: run `python3 <plugin-root>/tools/reviewfmt.py check FINDINGS` and read the verdict.
3. When the gate warns, fix the blocker/major findings or reshape the malformed lines before the review ships.
