# Contributing

Short rules for the shanewas-plugins marketplace catalog.

## Add a plugin

1. Scaffold it: `./add-plugin.ps1 -Name "my-tool" -Description "..."`.
2. Fill in `skills/`, `commands/`, `agents/`, `hooks/`, and `tools/`.
3. Keep the three manifests in sync: `.claude-plugin/plugin.json`,
   `package.json`, `gemini-extension.json`.

## Versioning

- Root `VERSION` holds the catalog release version.
- Every `marketplace.json` entry and every plugin manifest carries that
  same version. `tests/test_manifests.py::test_versions_in_sync`
  enforces it; see `CHANGELOG.md` for the bump rule.
- Document user-visible changes under `[Unreleased]` in `CHANGELOG.md`.

## Checks

- `python3 tests/run.py` must exit 0 (this is also the CI gate).
- If `muse` is installed: `muse plugins validate plugins/<name>`
  must report valid for the touched plugin.
- Keep new code dependency-free (stdlib only) unless the plugin
  genuinely needs a runtime dependency; declare it in `package.json`.

## Pull requests

- One plugin or one concern per PR, with tests for new behavior.
- Do not commit secrets, credentials, or machine-local paths.
