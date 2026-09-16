"""audit-trail ledger tests: append fail-open plus digest shapes."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

LEDGER = ROOT / "plugins" / "audit-trail" / "tools" / "ledger.py"
FIXTURES = ROOT / "tests" / "fixtures" / "audit"

V1_FIELDS = ("schema", "ts", "session", "turn", "tool", "file",
             "lines_added", "lines_removed", "claim_refs")


def _env_with_ledger(path):
    env = dict(os.environ)
    env["AUDIT_TRAIL_LEDGER"] = str(path)
    return env


def _run(*args, env=None, stdin_text=None):
    return subprocess.run(
        [sys.executable, str(LEDGER), *args],
        capture_output=True, text=True, timeout=60,
        env=dict(os.environ) if env is None else env, input=stdin_text)


def _append(stdin_text, ledger_path):
    return _run("append", env=_env_with_ledger(ledger_path),
                stdin_text=stdin_text)


def _read_records(ledger_path):
    lines = Path(ledger_path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_append_writes_valid_v1_jsonl():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        event = (FIXTURES / "hook-event.json").read_text(encoding="utf-8")
        proc = _append(event, ledger_path)
        assert proc.returncode == 0, "append exited %d: %s" % (
            proc.returncode, proc.stderr[:200])
        records = _read_records(ledger_path)
        assert len(records) == 1, "want 1 record, got %d" % len(records)
        record = records[0]
        for field in V1_FIELDS:
            assert field in record, "record lacks field %r: %r" % (field, record)
        assert record["schema"] == "v1", "schema %r, want 'v1'" % (
            record.get("schema"),)
        assert record["file"] == "src/widget.py", "file %r" % record["file"]
        assert record["tool"] == "Edit", "tool %r" % record["tool"]
        assert record["session"] == "sess-1", "session %r" % record["session"]
        assert record["turn"] == 3, "turn %r" % (record["turn"],)
        assert record["lines_added"] == 12, "added %r" % record["lines_added"]
        assert record["lines_removed"] == 4, "removed %r" % record["lines_removed"]
        assert record["claim_refs"] == ["claim-7"], "claims %r" % (
            record["claim_refs"],)


def test_append_flat_variant():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        event = json.dumps({"tool": "Write", "file": "a/b.txt",
                            "session": "s2", "turn": 9,
                            "edited_lines": {"added": 2, "removed": 0}})
        proc = _append(event, ledger_path)
        assert proc.returncode == 0, "flat append exited %d" % proc.returncode
        (record,) = _read_records(ledger_path)
        assert record["schema"] == "v1", "flat record schema %r" % (
            record.get("schema"),)
        assert (record["tool"], record["file"], record["turn"]) == (
            "Write", "a/b.txt", 9)


def test_append_bad_stdin_fail_open():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        proc = _append("{not json", ledger_path)
        assert proc.returncode == 0, "bad stdin append exited %d" % (
            proc.returncode,)
        assert "audit-trail" in proc.stderr, "bad stdin needs a stderr note"
        assert not ledger_path.exists(), "bad stdin must not write a ledger"


def test_append_empty_stdin_fail_open():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        proc = _append("", ledger_path)
        assert proc.returncode == 0, "empty stdin append exited %d" % (
            proc.returncode,)
        assert "audit-trail" in proc.stderr, "empty stdin needs a stderr note"
        assert not ledger_path.exists(), "empty stdin must not write a ledger"


def test_append_non_object_fail_open():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        proc = _append("[1, 2]", ledger_path)
        assert proc.returncode == 0, "non-object append exited %d" % (
            proc.returncode,)
        assert not ledger_path.exists(), "non-object must not write a ledger"


def test_append_missing_file_fail_open():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        proc = _append(json.dumps({"tool_name": "Edit"}), ledger_path)
        assert proc.returncode == 0, "fileless append exited %d" % (
            proc.returncode,)
        assert "audit-trail" in proc.stderr, "fileless event needs a stderr note"
        assert not ledger_path.exists(), "fileless event must not write a ledger"


def test_append_creates_parent_dirs():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / ".audit-trail" / "nested" / "ledger.jsonl"
        proc = _append(json.dumps({"tool": "Edit", "file": "x.py"}),
                       ledger_path)
        assert proc.returncode == 0, "nested append exited %d: %s" % (
            proc.returncode, proc.stderr[:200])
        assert _read_records(ledger_path)[0]["file"] == "x.py"


def test_schema_version_on_every_record():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        for name in ("one.py", "two.py"):
            proc = _append(json.dumps({"tool": "Edit", "file": name}),
                           ledger_path)
            assert proc.returncode == 0
        records = _read_records(ledger_path)
        assert len(records) == 2, "want 2 records, got %d" % len(records)
        for record in records:
            assert record.get("schema") == "v1", "record lacks schema v1: %r" % (
                record,)


def test_digest_text_shape():
    proc = _run("digest", str(FIXTURES / "sample-ledger.jsonl"))
    assert proc.returncode == 0, "digest exited %d: %s" % (
        proc.returncode, proc.stderr[:200])
    assert "3 edits across 2 files" in proc.stdout, "digest header: %r" % (
        proc.stdout[:200],)
    assert "(+25/-7)" in proc.stdout, "digest totals: %r" % proc.stdout[:300]
    assert "src/widget.py (+20/-5, 2 edits, turns 3, 4)" in proc.stdout, (
        "widget line: %r" % proc.stdout)
    assert "docs/notes.md (+5/-2, 1 edit, turn 5)" in proc.stdout, (
        "notes line: %r" % proc.stdout)


def test_digest_json_shape():
    proc = _run("digest", str(FIXTURES / "sample-ledger.jsonl"), "--json")
    assert proc.returncode == 0, "json digest exited %d" % proc.returncode
    try:
        summary = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError("digest --json printed invalid JSON: %r" % (
            proc.stdout[:200],))
    assert summary["edits"] == 3, "edits %r" % summary.get("edits")
    assert (summary["lines_added"], summary["lines_removed"]) == (25, 7)
    assert len(summary["files"]) == 2, "files %r" % summary.get("files")
    first = summary["files"][0]
    assert first["file"] == "src/widget.py", "first file %r" % first
    assert (first["edits"], first["lines_added"],
            first["lines_removed"], first["turns"]) == (2, 20, 5, [3, 4])


def test_digest_missing_ledger_fail_open():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        missing = Path(tmp) / "no-ledger.jsonl"
        proc = _run("digest", str(missing))
        assert proc.returncode == 0, "missing digest exited %d" % (
            proc.returncode,)
        assert "no ledger yet" in proc.stdout, "missing digest note: %r" % (
            proc.stdout[:200],)
        proc = _run("digest", str(missing), "--json")
        assert proc.returncode == 0, "missing json digest exited %d" % (
            proc.returncode,)
        summary = json.loads(proc.stdout)
        assert summary["edits"] == 0 and summary["files"] == [], (
            "missing json digest must be empty: %r" % summary)


def test_digest_skips_corrupt_lines():
    with tempfile.TemporaryDirectory(prefix="audit-trail-") as tmp:
        ledger_path = Path(tmp) / "ledger.jsonl"
        good = (FIXTURES / "sample-ledger.jsonl").read_text(encoding="utf-8")
        ledger_path.write_text("{broken\n" + good + "[1]\n", encoding="utf-8")
        proc = _run("digest", str(ledger_path))
        assert proc.returncode == 0, "corrupt digest exited %d" % (
            proc.returncode,)
        assert "3 edits across 2 files" in proc.stdout, (
            "corrupt lines must not hide valid edits: %r" % proc.stdout[:200])
        assert "skipped 2 corrupt" in proc.stderr, (
            "corrupt lines need a stderr note: %r" % proc.stderr[:200])
