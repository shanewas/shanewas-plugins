"""Frontmatter lint over every SKILL.md and SKILL-adjacent document.

Covers plugins/*/skills/*/SKILL.md (strict schema) plus the agent and
command markdown that ships alongside skills (adjacent schema).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT, read_frontmatter, require_non_empty


def _skill_files():
    return sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))


def test_skill_files_exist():
    files = _skill_files()
    assert files, "no SKILL.md fixtures found under plugins/*/skills/*/"


def test_skill_frontmatter_schema():
    for path in _skill_files():
        fields, body = read_frontmatter(path)
        require_non_empty(path, fields, "name", "description")
        assert fields["name"] == path.parent.name, (
            "%s: frontmatter name %r must match skill directory %r"
            % (path, fields["name"], path.parent.name)
        )
        assert body.strip(), "%s: SKILL.md body must not be empty" % path


def test_agent_frontmatter_schema():
    files = sorted(ROOT.glob("plugins/*/agents/*.md"))
    for path in files:
        fields, _ = read_frontmatter(path)
        require_non_empty(path, fields, "name", "description")


def test_command_frontmatter_schema():
    files = sorted(ROOT.glob("plugins/*/commands/*.md"))
    for path in files:
        fields, _ = read_frontmatter(path)
        require_non_empty(path, fields, "description")
