# Muse native hooks: TBD

No local Muse hook manifest or event schema was found during the build
session, so this plugin ships no Muse hook wiring. The CLI still works
under Muse today:

- Run `git diff HEAD -- | python3 tools/diffgate.py check` to gate the
  working tree on demand.
- Run `python3 tools/diffgate.py check CHANGES.diff` against a saved
  diff file; set `DIFF_GATE_MODE=block` when a nonzero exit must fail
  the step.

Native hook support lands once a Muse hook envelope can be copied from
a real local install instead of guessed.
