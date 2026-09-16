"""review-pair packaging tests: manifests, hooks, and tool presence.

Mirrors the slop-gate fileset contract without touching the marketplace
catalog: the three native manifests parse, versions match the root VERSION,
and every shipped hook file carries a valid envelope pointing at tools/reviewfmt.py.
"""

import json
import py_compile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

PLUGIN = ROOT / "plugins" / "review-pair"
MANIFEST_FILES = (
    ".claude-plugin/plugin.json",
    "package.json",
    "gemini-extension.json",
)


def _load_json(rel):
    path = PLUGIN / rel
    assert path.is_file(), "review-pair: missing %s" % rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError("review-pair %s: invalid JSON: %s" % (rel, exc))


def test_manifests_parse_with_name_and_version():
    for rel in MANIFEST_FILES:
        data = _load_json(rel)
        assert data.get("name"), "review-pair %s missing 'name'" % rel
        assert data.get("version"), "review-pair %s missing 'version'" % rel


def test_manifest_versions_match_root():
    root_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert root_version, "VERSION file must not be empty"
    for rel in MANIFEST_FILES:
        data = _load_json(rel)
        assert data.get("version") == root_version, (
            "review-pair %s version %r != root VERSION %r"
            % (rel, data.get("version"), root_version))


def test_tool_and_shim_present():
    tool = PLUGIN / "tools" / "reviewfmt.py"
    assert tool.is_file(), "review-pair: missing tools/reviewfmt.py"
    py_compile.compile(str(tool), doraise=True)
    package = _load_json("package.json")
    assert package.get("main") == "plugin.js", "package.json main must be plugin.js"
    assert (PLUGIN / "plugin.js").is_file(), "review-pair: missing plugin.js"
    shim = (PLUGIN / "plugin.js").read_text(encoding="utf-8")
    assert "tools/reviewfmt.py" in shim or "tools\", \"reviewfmt.py" in shim, (
        "plugin.js must call tools/reviewfmt.py")


def test_claude_hooks_envelope():
    data = _load_json("hooks/hooks.json")
    post = (data.get("hooks") or {}).get("PostToolUse")
    assert post, "hooks/hooks.json lacks PostToolUse"
    commands = [hook.get("command", "")
                for entry in post for hook in entry.get("hooks", [])]
    assert any("tools/reviewfmt.py" in cmd for cmd in commands), (
        "hooks/hooks.json must route to tools/reviewfmt.py, got %r" % (commands,))
    assert any("CLAUDE_PLUGIN_ROOT" in cmd for cmd in commands), (
        "hooks/hooks.json must use ${CLAUDE_PLUGIN_ROOT}, got %r" % (commands,))


def test_codex_hooks_envelope():
    data = _load_json("hooks.json")
    post = (data.get("hooks") or {}).get("PostToolUse")
    assert post, "hooks.json lacks PostToolUse"
    commands = [hook.get("command", "")
                for entry in post for hook in entry.get("hooks", [])]
    assert any(cmd.startswith("python3 ./tools/reviewfmt.py") for cmd in commands), (
        "hooks.json must call ./tools/reviewfmt.py relative to the plugin root, "
        "got %r" % (commands,))


def test_antigravity_snippet_shape():
    data = _load_json("hooks/antigravity-hooks.json")
    entry = data.get("review-pair")
    assert entry, "antigravity snippet lacks the review-pair entry"
    post = entry.get("PostToolUse") or []
    assert post, "antigravity snippet lacks PostToolUse"
    assert post[0].get("matcher") == "write_to_file|replace_file_content", (
        "antigravity matcher must be write_to_file|replace_file_content")
    commands = [hook.get("command", "")
                for hook in post[0].get("hooks", [])]
    assert any("tools/reviewfmt.py" in cmd for cmd in commands), (
        "antigravity snippet must route to tools/reviewfmt.py")


def test_muse_tbd_note_present():
    note = PLUGIN / "docs" / "muse-hooks-TBD.md"
    assert note.is_file(), "review-pair: missing docs/muse-hooks-TBD.md"
    body = note.read_text(encoding="utf-8")
    assert "reviewfmt.py" in body, "Muse TBD note must name the CLI fallback"
