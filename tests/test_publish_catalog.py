"""Publish-gate catalog completeness checks (stdlib only).

test_manifests.py validates each marketplace entry on its own terms;
these tests guard the catalog as a whole: every shipped plugin
directory must be listed exactly once, so a new plugin can never land
in plugins/ without a marketplace entry (or vice versa).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT


def _catalog_entries():
    path = ROOT / ".claude-plugin" / "marketplace.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError("marketplace.json: invalid JSON: %s" % exc)
    assert isinstance(data.get("plugins"), list), (
        "marketplace.json: 'plugins' must be a list"
    )
    return data["plugins"]


def test_catalog_covers_every_plugin_dir():
    entries = _catalog_entries()
    listed = sorted(e.get("name") for e in entries)
    shipped = sorted(p.name for p in (ROOT / "plugins").iterdir()
                     if p.is_dir())
    assert shipped, "plugins/: no plugin directories found"
    missing = [name for name in shipped if name not in listed]
    assert not missing, (
        "marketplace.json: no catalog entry for shipped plugin(s): %s"
        % ", ".join(missing)
    )
    orphaned = [name for name in listed if name not in shipped]
    assert not orphaned, (
        "marketplace.json: catalog entry(s) with no plugin dir: %s"
        % ", ".join(orphaned)
    )


def test_catalog_names_unique_and_source_matches():
    seen = set()
    for entry in _catalog_entries():
        name = entry.get("name")
        assert name and name not in seen, (
            "marketplace.json: duplicate or empty plugin name: %r" % (entry,)
        )
        seen.add(name)
        source = entry.get("source") or ""
        assert Path(source).name == name, (
            "marketplace.json: %r source dir %r must match entry name"
            % (name, source)
        )
