# Muse native hooks: TBD

No local Muse hook manifest or event schema was found during the build
session, so this plugin ships no Muse hook wiring. The CLI still works
under Muse today:

- Pipe a hook event into `python3 tools/ledger.py append` to log an edit.
- Run `python3 tools/ledger.py digest` to review the ledger; add `--json`
  when a script consumes the output.

Native hook support lands once a Muse hook envelope can be copied from
a real local install instead of guessed.
