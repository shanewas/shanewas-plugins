# Changelog

All notable changes to the shanewas-plugins marketplace catalog are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the catalog uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-09-15

### Added

- Initial universal agent marketplace scaffold.
- `core-tools` plugin: `git-summary` skill, `/summary` command, and
  `repo-auditor` agent with Claude Code, Antigravity, OpenCode, Hermes,
  and Muse Code install paths.
- `slop-gate` plugin: AI-slop scorer and PostToolUse edit gate
  (`tools/slop.py`, warn/block thresholds, cross-harness hooks).
- `audit-trail` plugin: JSONL edit ledger plus per-file review digests.
- `minimal-diff` plugin: diff-size gate for single-review changes.
- `verify-done` plugin: done-claim evidence gate (build/test/artifact).
- `review-pair` plugin: machine-readable review-findings shape gate.
- `commit-gate` plugin: commit-message and staged-file gate (shape,
  AI-trailer, and banned-extension checks).
- Repo foundation: zero-dependency fixture tests (`tests/run.py`),
  frontmatter lint over every `SKILL.md` and skill-adjacent document,
  marketplace/manifest consistency checks, CI workflow, root `VERSION`
  file, and this changelog.
- README install-matrix appendix covering the five supported harnesses.
- `add-plugin.ps1` generator for new cross-agent packages.

## Versioning scheme

- The root `VERSION` file holds the marketplace catalog release version.
- Each entry in `.claude-plugin/marketplace.json` carries its own
  `version`, kept in sync with the root `VERSION` on every catalog
  release (`tests/test_manifests.py::test_versions_in_sync` enforces this).
- Each plugin directory repeats that same version in its three native
  manifests: `.claude-plugin/plugin.json`, `package.json`, and
  `gemini-extension.json`.
- Per-plugin standalone `VERSION` files are reserved for a future unit;
  until then the three manifests plus the marketplace entry are the
  canonical per-plugin version record. No `VERSION` file is placed
  inside `plugins/core-tools/` by unit 0.
- Bump rule: patch for skill/command doc fixes, minor for new
  skills/plugins/harnesses, major for manifest schema or layout breaks.

[Unreleased]: https://github.com/shanewas/shanewas-plugins/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/shanewas/shanewas-plugins/releases/tag/v1.0.0
