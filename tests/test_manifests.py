"""Marketplace and per-plugin manifest consistency checks (stdlib only).

Enforces the VERSION scheme documented in CHANGELOG.md: the root VERSION
file tracks the catalog release and every plugin manifest version stays
in sync with the marketplace.json entry.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

MANIFEST_FILES = (
    ".claude-plugin/plugin.json",
    "package.json",
    "gemini-extension.json",
)


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError("%s: invalid JSON: %s" % (path, exc))


def _marketplace_plugins():
    data = _load_json(ROOT / ".claude-plugin" / "marketplace.json")
    assert isinstance(data.get("plugins"), list), (
        "marketplace.json: 'plugins' must be a list"
    )
    assert data["plugins"], "marketplace.json: 'plugins' must not be empty"
    return data["plugins"]


def test_marketplace_entries_have_source_dirs():
    for entry in _marketplace_plugins():
        for key in ("name", "version", "source"):
            assert entry.get(key), (
                "marketplace.json: plugin entry missing %r: %r" % (key, entry)
            )
        source = ROOT / entry["source"]
        assert source.is_dir(), (
            "marketplace.json: source dir missing for %r: %s"
            % (entry["name"], entry["source"])
        )


def test_plugin_manifests_parse():
    for entry in _marketplace_plugins():
        plugin_dir = ROOT / entry["source"]
        for rel in MANIFEST_FILES:
            manifest = plugin_dir / rel
            assert manifest.is_file(), "%s: missing %s" % (
                entry["name"], rel)
            data = _load_json(manifest)
            assert data.get("name"), "%s: %s missing 'name'" % (
                entry["name"], rel)
            assert data.get("version"), "%s: %s missing 'version'" % (
                entry["name"], rel)


def test_versions_in_sync():
    root_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert root_version, "VERSION file must not be empty"
    for entry in _marketplace_plugins():
        assert entry["version"] == root_version, (
            "marketplace.json: %s version %r != root VERSION %r"
            % (entry["name"], entry["version"], root_version)
        )
        plugin_dir = ROOT / entry["source"]
        for rel in MANIFEST_FILES:
            data = _load_json(plugin_dir / rel)
            assert data.get("version") == root_version, (
                "%s: %s version %r != root VERSION %r"
                % (entry["name"], rel, data.get("version"), root_version)
            )
