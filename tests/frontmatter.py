"""Minimal YAML-frontmatter reader for the fixture tests (stdlib only).

Supports the flat `key: value` frontmatter used by SKILL.md, agent, and
command documents in this repo. Not a general YAML parser by design.
"""

from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT = TESTS_DIR.parent


def read_frontmatter(path):
    """Return (fields, body) for a markdown file with a --- block.

    Raises AssertionError with a file-specific message on any structural
    problem so test failures point at the offending document.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", (
        "%s: missing opening --- frontmatter fence" % path
    )
    try:
        closing = next(
            i for i, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        raise AssertionError("%s: missing closing --- frontmatter fence" % path)
    fields = {}
    for lineno, line in enumerate(lines[1:closing], start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assert ":" in stripped, (
            "%s:%d: frontmatter line is not 'key: value': %r"
            % (path, lineno, line)
        )
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        assert key, "%s:%d: empty frontmatter key" % (path, lineno)
        assert key not in fields, (
            "%s:%d: duplicate frontmatter key %r" % (path, lineno, key)
        )
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        fields[key] = value
    body = "\n".join(lines[closing + 1:])
    return fields, body


def require_non_empty(path, fields, *keys):
    """Assert that each named frontmatter key exists and is non-empty."""
    for key in keys:
        assert key in fields, "%s: missing required frontmatter key %r" % (
            path, key)
        assert fields[key].strip(), (
            "%s: frontmatter key %r must not be empty" % (path, key))
