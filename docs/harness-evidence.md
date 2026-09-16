# Harness install evidence (plan 007)

One hands-on spike per harness, probe plugin `core-tools`, dated 2026-09-16.
Worktree `/tmp/shanewas-exec` at `725948b` (includes plan 006 native Muse hooks;
upstream GitHub snapshot predates 006 — see Muse section).

## Claude Code

Commands (Windows `claude.exe` driven from WSL; version first):

```
$ /mnt/c/Users/san/.local/bin/claude.exe --version
2.1.252 (Claude Code)

$ claude.exe plugin marketplace add shanewas/shanewas-plugins
Adding marketplace…SSH not configured, cloning via HTTPS: https://github.com/shanewas/shanewas-plugins.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): https://github.com/shanewas/shanewas-plugins.git
Clone complete, validating marketplace…
Cleaning up old marketplace cache…
✔ Successfully added marketplace: shanewas-plugins (declared in user settings)

$ claude.exe plugin install core-tools@shanewas-plugins
Installing plugin "core-tools@shanewas-plugins"...✔ Successfully installed plugin: core-tools@shanewas-plugins (scope: user)

$ claude.exe plugin list   # excerpt; full listing showed all pre-existing plugins plus:
  ❯ core-tools@shanewas-plugins
    Version: 1.0.0
    Scope: user
    Status: ✔ enabled

$ claude.exe plugin marketplace list   # excerpt:
  ❯ shanewas-plugins
    Source: GitHub (shanewas/shanewas-plugins)

$ find /mnt/c/Users/san/.claude/plugins/cache/shanewas-plugins -maxdepth 4
.../cache/shanewas-plugins/core-tools/1.0.0/.claude-plugin/plugin.json
.../core-tools/1.0.0/agents/repo-auditor.md
.../core-tools/1.0.0/commands/summary.md
.../core-tools/1.0.0/skills/git-summary
```

Isolation note: `CLAUDE_CONFIG_DIR` pointing at a fresh temp dir was IGNORED
(temp dir stayed empty; state landed in the real `C:\Users\san\.claude`).
Rolled back immediately after capturing evidence:
`plugin uninstall core-tools@shanewas-plugins` ✔,
`plugin marketplace remove shanewas-plugins` ✔, orphaned cache dir removed,
`grep -ri shanewas settings.json installed_plugins.json known_marketplaces.json`
→ no matches. Real config restored to pre-spike state.

Result: VERIFIED

## Muse Code

Isolation: `HOME=<tempdir>` alone disables plugins
(`plugins are not available in this build`, exit 2) because the feature gate
lives in `$HOME/.local/share/muse/feature-config/7075626c6963.json`
(`"plugins": true`, non-secret cache). Copied only that file into temp HOME;
all state below landed under `/tmp/musehome-SeHsDr`, real HOME untouched.
`muse --version` → `Muse Code 1.3.0 (1.3.0-R3057.1)`.

```
$ HOME=$TH muse plugins marketplace list --json
{"marketplaces": [], "warnings": []}

$ HOME=$TH muse plugins marketplace add shanewas-plugins https://github.com/shanewas/shanewas-plugins
shanewas-plugins	plugins=7	source=https://github.com/shanewas/shanewas-plugins

$ HOME=$TH muse plugins install core-tools@shanewas-plugins
diagnostic=unsupported-field ... summary.md message=Claude command frontmatter field `context` is not modelled and is ignored
diagnostic=unsupported-field ... SKILL.md message=Claude skill frontmatter field `platforms` is not used by this runtime
diagnostic=unsupported-capability ... message=Claude conventional source `agents/` declares unsupported behavior
diagnostic=unsupported-field ... message=Claude manifest field `author` is presentation-only and is not imported
installed	core-tools	1.0.0	marketplace=shanewas-plugins	enabled=true	trust=user-local	provenance=marketplace-user-added	cache=/tmp/musehome-SeHsDr/.local/share/muse/plugins/cache/local/core-tools/b3c57b0f.../package

$ HOME=$TH muse plugins list
core-tools	1.0.0	enabled=true active=true trust=user-local provenance=marketplace-user-added valid=true diagnostics=4

$ HOME=$TH muse plugins inspect core-tools
core-tools	1.0.0	enabled=true active=true trust=user-local valid=true skills=1 commands=1 hooks=0 mcp=0 reminders=0 cache=/tmp/musehome-SeHsDr/.../package

$ HOME=$TH muse plugins validate plugins/core-tools
diagnostic=unsupported-field ... (same 4 warnings as install)
valid	core-tools	claude-compatible	skills=1 commands=1 hooks=0 mcp=0 reminders=0 diagnostics=4
```

Native-hook firing (006): the Git snapshot predates 006
(`.../source/plugins/commit-gate/.muse-plugin/`: No such file or directory —
worktree branch `advisor/execute-all` is local-only), so a second marketplace
was added from the local worktree to exercise the 006 manifests:

```
$ HOME=$TH muse plugins marketplace add local007 /tmp/shanewas-exec
local007	plugins=7	source=/tmp/shanewas-exec

$ HOME=$TH muse plugins install commit-gate@local007
diagnostic=multiple-manifests severity=warning ... message=selected `.muse-plugin/plugin.json`; ignoring `.claude-plugin/plugin.json`
installed	commit-gate	1.0.0	marketplace=local007	enabled=true	trust=user-local	provenance=marketplace-user-added	cache=/tmp/musehome-SeHsDr/.../commit-gate/8727b50e.../package
warning	third-party plugin: hooks require review before activation; skills and commands are active without review while the plugin is enabled

$ HOME=$TH muse plugins inspect commit-gate
commit-gate	1.0.0	enabled=true active=true trust=user-local valid=true skills=1 commands=1 hooks=1 mcp=0 reminders=0 cache=/tmp/musehome-SeHsDr/.../package
runtime-capability	plugin:commit-gate:hook:commit-check	status=review_needed

$ printf '{"event":"PostToolUse","stdin":"{}"}' > /tmp/hook-fixture.json
$ HOME=$TH muse plugins hook test commit-gate:commit-check --fixture /tmp/hook-fixture.json --json
{
  "decision": { ... "should_block": false, ... },
  "records": 2,
  "terminals": [
    {
      "duration_ms": 42,
      "event": "post_tool_use",
      "exit_code": 0,
      "hook_key": "plugin:commit-gate:hook:commit-check",
      "status": "failed",
      "stderr": "commit-gate: no --message-file given\n",
      "stdout": "{\n  \"ok\": true,\n  \"violations\": [],\n  \"mode\": \"warn\",\n  ...\n}\n"
    }
  ]
}
```

Hook verdict: the native hook FIRED — `tools/commitcheck.py` executed
(exit 0, 42 ms, real gate JSON on stdout). The harness marks the terminal
`failed` only because the tool's output JSON shape (`message` key) does not
match the PostToolUse hook-output schema
(`error: unsupported \`message\` in output of PostToolUse hook output`).
That is a tool-output/harness-schema mismatch, not an install-path failure;
flagged for a follow-up, out of scope for this docs plan (no plugin edits).

Result: VERIFIED

## OpenCode

```
$ command -v node; echo "node-exit=$?"
node-exit=127
$ command -v opencode antigravity hermes gemini; echo "harness-exit=$?"
harness-exit=127
```

No `node` and no `opencode` binary, so `node --check` and a real load run
were impossible. Static checks only (temp dir `/tmp/spike007-BYqGKK`):

```
$ python3 -c "import json;print(json.load(open('plugins/core-tools/package.json'))['main'])"
plugin.js
$ head -8 plugins/core-tools/plugin.js
export const plugin = async (ctx) => {
  return {
    name: "core-tools",
    ...
```

Wrote the documented `opencode.json` shape to temp (never to real
`~/.config`); contents validate as JSON but no runtime consumed it.

Result: TBD (no node or opencode binary in this environment)

## Google Antigravity

No Antigravity/Gemini CLI binary in this environment
(`command -v antigravity gemini` → 127) and the real target
`~/.gemini/extensions/` is off-limits, so runtime discovery could not be
confirmed. Temp-dir copy per docs (`/tmp/spike007-BYqGKK/gemini-extensions`):

```
$ cp -r plugins/core-tools $T/gemini-extensions/core-tools
$ python3 -c "import json;print('gemini-extension.json OK:',json.load(open('$T/gemini-extensions/core-tools/gemini-extension.json'))['name'])"
gemini-extension.json OK: core-tools
$ find $T/gemini-extensions/core-tools -maxdepth 1
.../core-tools/skills
.../core-tools/plugin.js
.../core-tools/package.json
.../core-tools/gemini-extension.json
.../core-tools/commands
.../core-tools/agents
.../core-tools/.claude-plugin
```

Layout + discovery manifest are present and valid, but nothing performed
Antigravity-side discovery.

Result: TBD (no Antigravity binary in this environment; real ~/.gemini off-limits)

## Hermes

No `hermes` binary in this environment (`command -v hermes` → 127), so
Hermes-side listing/loading could not be confirmed. Temp-dir skills copy
per docs (`/tmp/spike007-BYqGKK/hermes-skills`):

```
$ cp -r plugins/core-tools/skills/git-summary $T/hermes-skills/git-summary
$ ls $T/hermes-skills/git-summary/
SKILL.md
```

Result: TBD (no hermes binary in this environment)

## Round 2 (2026-09-16) — OpenCode binary spike

Installed opencode 1.18.31 user-local (`~/.opencode/bin`, no sudo).
Project config IS read (`loading path=/tmp/ocspike/opencode.json` in
`--print-logs --log-level DEBUG`), but file-path `plugin` entries
produce zero observable load signal:

- Positive: `plugin: ["/tmp/shanewas-exec/plugins/core-tools/plugin.js"]`
  → `opencode run` clean, exit 0, no plugin mentions in DEBUG logs.
- Negative: nonexistent path → identical clean run (proves nothing).
- Throwing control (`throw new Error("PROBE-BOOM")`): silent in
  project config, in `file://` URL form, AND in global
  `~/.config/opencode/opencode.jsonc` (backed up, patched, ran,
  restored byte-identical — `cmp` clean).

`opencode plugin <module>` only accepts npm module names (no node/npm
here). Conclusion: the documented "reference `plugin.js` in
`opencode.json`" path is UNVERIFIABLE on opencode 1.18.31 — file
entries are silently ignored. Likely needs an npm-packaged plugin via
the `opencode plugin` flow. Row stays TBD.

Hermes / Antigravity round 2: still no binaries and no public CLI
install path found — rows stay TBD.
