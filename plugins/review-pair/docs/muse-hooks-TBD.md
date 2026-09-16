# Muse native hooks: TBD

No local Muse hook manifest or event schema was found during the build
session, so this plugin ships no Muse hook wiring. The CLI still works
under Muse today:

- Run `python3 tools/reviewfmt.py check FINDINGS.txt` to validate
  findings on demand.
- Run `python3 tools/reviewfmt.py check FINDINGS.txt --json` when a
  machine-readable report must feed an audit ledger.
- Set `REVIEW_PAIR_MODE=block` when a nonzero exit must fail the step.

Native hook support lands once a Muse hook envelope can be copied from
a real local install instead of guessed.
