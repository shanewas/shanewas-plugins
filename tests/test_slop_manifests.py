"""slop-gate packaging tests: manifests, hooks, and tool presence.

Mirrors the core-tools fileset contract without touching the marketplace
catalog: the three native manifests parse, versions match the root VERSION,
and every shipped hook file carries a valid envelope pointing at tools/slop.py.
"""

import json
import py_compile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

PLUGIN = ROOT / "plugins" / "slop-gate"
MANIFEST_FILES = (
    ".claude-plugin/plugin.json",
    ".muse-plugin/plugin.json",
    "package.json",
    "gemini-extension.json",
)


def _load_json(rel):
    path = PLUGIN / rel
    assert path.is_file(), "slop-gate: missing %s" % rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError("slop-gate %s: invalid JSON: %s" % (rel, exc))


def test_manifests_parse_with_name_and_version():
    for rel in MANIFEST_FILES:
        data = _load_json(rel)
        assert data.get("name"), "slop-gate %s missing 'name'" % rel
        assert data.get("version"), "slop-gate %s missing 'version'" % rel


def test_manifest_versions_match_root():
    root_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert root_version, "VERSION file must not be empty"
    for rel in MANIFEST_FILES:
        data = _load_json(rel)
        assert data.get("version") == root_version, (
            "slop-gate %s version %r != root VERSION %r"
            % (rel, data.get("version"), root_version))


def test_tool_and_shim_present():
    slop = PLUGIN / "tools" / "slop.py"
    assert slop.is_file(), "slop-gate: missing tools/slop.py"
    py_compile.compile(str(slop), doraise=True)
    package = _load_json("package.json")
    assert package.get("main") == "plugin.js", "package.json main must be plugin.js"
    assert (PLUGIN / "plugin.js").is_file(), "slop-gate: missing plugin.js"
    shim = (PLUGIN / "plugin.js").read_text(encoding="utf-8")
    assert "tools/slop.py" in shim or "tools\", \"slop.py" in shim, (
        "plugin.js must call tools/slop.py")


def test_claude_hooks_envelope():
    data = _load_json("hooks/hooks.json")
    post = (data.get("hooks") or {}).get("PostToolUse")
    assert post, "hooks/hooks.json lacks PostToolUse"
    commands = [hook.get("command", "")
                for entry in post for hook in entry.get("hooks", [])]
    assert any("tools/slop.py" in cmd for cmd in commands), (
        "hooks/hooks.json must route to tools/slop.py, got %r" % (commands,))
    assert any("CLAUDE_PLUGIN_ROOT" in cmd for cmd in commands), (
        "hooks/hooks.json must use ${CLAUDE_PLUGIN_ROOT}, got %r" % (commands,))


def test_codex_hooks_envelope():
    data = _load_json("hooks.json")
    post = (data.get("hooks") or {}).get("PostToolUse")
    assert post, "hooks.json lacks PostToolUse"
    commands = [hook.get("command", "")
                for entry in post for hook in entry.get("hooks", [])]
    assert any(cmd.startswith("python3 ./tools/slop.py") for cmd in commands), (
        "hooks.json must call ./tools/slop.py relative to the plugin root, "
        "got %r" % (commands,))


def test_antigravity_snippet_shape():
    data = _load_json("hooks/antigravity-hooks.json")
    entry = data.get("slop-gate")
    assert entry, "antigravity snippet lacks the slop-gate entry"
    post = entry.get("PostToolUse") or []
    assert post, "antigravity snippet lacks PostToolUse"
    assert post[0].get("matcher") == "write_to_file|replace_file_content", (
        "antigravity matcher must be write_to_file|replace_file_content")
    commands = [hook.get("command", "")
                for hook in post[0].get("hooks", [])]
    assert any("tools/slop.py" in cmd for cmd in commands), (
        "antigravity snippet must route to tools/slop.py")


def test_muse_hooks_envelope():
    data = _load_json(".muse-plugin/plugin.json")
    hooks = (data.get("capabilities") or {}).get("hooks") or []
    post = [hook for hook in hooks if hook.get("event") == "PostToolUse"]
    assert post, ".muse-plugin/plugin.json lacks a PostToolUse hook"
    for hook in post:
        assert isinstance(hook.get("command"), list), (
            ".muse-plugin/plugin.json hook command must be argv, got %r"
            % (hook.get("command"),))
    commands = [" ".join(hook.get("command", [])) for hook in post]
    assert any("tools/slop.py" in cmd for cmd in commands), (
        ".muse-plugin/plugin.json must route to tools/slop.py, got %r"
        % (commands,))
