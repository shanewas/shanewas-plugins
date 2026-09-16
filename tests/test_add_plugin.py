"""add-plugin.sh scaffold tests: layout, refusal, required name, JSON validity.

Runs the bash scaffolder against a temp --root with the fixture
marketplace stub, so the real .claude-plugin/marketplace.json is untouched.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "add-plugin.sh"
FIXTURE_MARKETPLACE = ROOT / "tests" / "fixtures" / "add_plugin" / "marketplace.json"

DIRS = [".claude-plugin", "skills/my-tool", "commands", "agents"]
FILES = [
    ".claude-plugin/plugin.json",
    "gemini-extension.json",
    "package.json",
    "plugin.js",
    "skills/my-tool/SKILL.md",
]


def _make_root():
    tmp = Path(tempfile.mkdtemp(prefix="add-plugin-test-"))
    market_dir = tmp / ".claude-plugin"
    market_dir.mkdir(parents=True)
    shutil.copyfile(FIXTURE_MARKETPLACE, market_dir / "marketplace.json")
    return tmp


def _run(*args):
    return subprocess.run(
        ["bash", str(SCRIPT)] + list(args),
        capture_output=True, text=True, timeout=120)


def test_scaffold_creates_layout():
    tmp = _make_root()
    try:
        proc = _run("--root", str(tmp), "--name", "my-tool",
                    "--description", "Test tool")
        assert proc.returncode == 0, "scaffold exited %d: %s" % (
            proc.returncode, proc.stderr)
        plug = tmp / "plugins" / "my-tool"
        for rel in DIRS:
            assert (plug / rel).is_dir(), "missing dir %s" % rel
        for rel in FILES:
            assert (plug / rel).is_file(), "missing file %s" % rel
        with open(tmp / ".claude-plugin" / "marketplace.json",
                  encoding="utf-8") as fh:
            market = json.load(fh)
        assert len(market["plugins"]) == 1, "want 1 entry, got %d" % (
            len(market["plugins"]),)
        assert market["plugins"][0]["name"] == "my-tool"
        assert market["plugins"][0]["source"] == "./plugins/my-tool"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_scaffold_refuses_existing():
    tmp = _make_root()
    try:
        first = _run("--root", str(tmp), "--name", "my-tool")
        assert first.returncode == 0, "first run exited %d: %s" % (
            first.returncode, first.stderr)
        second = _run("--root", str(tmp), "--name", "my-tool")
        assert second.returncode != 0, "second run should refuse existing dir"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_scaffold_requires_name():
    tmp = _make_root()
    try:
        proc = _run("--root", str(tmp))
        assert proc.returncode != 0, "missing --name should exit nonzero"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_generated_json_parses():
    tmp = _make_root()
    try:
        proc = _run("--root", str(tmp), "--name", "my-tool",
                    "--description", "Test tool")
        assert proc.returncode == 0, "scaffold exited %d: %s" % (
            proc.returncode, proc.stderr)
        plug = tmp / "plugins" / "my-tool"
        found = sorted(plug.rglob("*.json"))
        assert len(found) >= 3, "want 3+ generated JSON files, got %d" % (
            len(found),)
        for path in found:
            with open(path, encoding="utf-8") as fh:
                try:
                    data = json.load(fh)
                except json.JSONDecodeError:
                    raise AssertionError("%s is not valid JSON" % path.name)
            assert data.get("name"), "%s missing name" % path.name
            assert data.get("version") == "1.0.0", "%s bad version" % path.name
            if path.name != "gemini-extension.json":
                assert data.get("author"), "%s missing author" % path.name
        skill = (plug / "skills" / "my-tool" / "SKILL.md").read_text(
            encoding="utf-8")
        assert skill.startswith("---\n"), "SKILL.md missing --- frontmatter"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit("run via python3 tests/run.py")
