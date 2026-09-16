# Muse native hooks: TBD

No local Muse hook manifest or event schema was found during the build
session, so this plugin ships no Muse hook wiring. The CLI still works
under Muse today:

- Run `python3 tools/slop.py score FILE` to check prose on demand.
- Run `python3 tools/slop.py check FILE` in scripts; set
  `SLOP_GATE_MODE=block` when a nonzero exit must fail the step.

Native hook support lands once a Muse hook envelope can be copied from
a real local install instead of guessed.
