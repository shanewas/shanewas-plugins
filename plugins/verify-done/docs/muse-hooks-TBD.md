# Muse native hooks: TBD

No local Muse hook manifest or event schema was found during the build
session, so this plugin ships no Muse hook wiring. The CLI still works
under Muse today:

- Run `python3 tools/donecheck.py check --claim CLAIM.md` to check a
  done claim on demand; add `--evidence LOG` for the files/commands log.
- Set `VERIFY_DONE_MODE=block` when a nonzero exit must fail the step.

Native hook support lands once a Muse hook envelope can be copied from
a real local install instead of guessed.
