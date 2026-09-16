---
description: Render the audit-trail ledger as a per-file review digest
argument-hint: "[ledger] (optional path to the ledger file)"
---

# Audit Command

1. Pick the ledger: use the argument when given, else `$AUDIT_TRAIL_LEDGER`, else `.audit-trail/ledger.jsonl`.
2. Run `python3 <plugin-root>/tools/ledger.py digest [LEDGER]` and read the per-file list.
3. Walk each file's line counts and turn refs before you sign off the review.
