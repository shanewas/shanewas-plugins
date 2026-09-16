"""review-pair check tests: ok-vs-warn exits, shape validation, fail-open."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

REVIEWFMT = ROOT / "plugins" / "review-pair" / "tools" / "reviewfmt.py"
FIXTURES = ROOT / "tests" / "fixtures" / "review"


def _warn_env():
    env = dict(os.environ)
    env.pop("REVIEW_PAIR_MODE", None)
    return env


def _run_check(*args, env=None, stdin_text=None):
    return subprocess.run(
        [sys.executable, str(REVIEWFMT), "check", *args],
        input=stdin_text, capture_output=True, text=True, timeout=60,
        env=_warn_env() if env is None else env)


def test_check_nit_only_passes():
    proc = _run_check(str(FIXTURES / "clean.txt"))
    assert proc.returncode == 0, "clean check exited %d" % proc.returncode
    assert "Review check: ok" in proc.stdout, (
        "clean check printed no ok verdict: %r" % (proc.stdout[:200],))
    assert "nit=3" in proc.stdout, (
        "clean check must report nit count: %r" % (proc.stdout[:200],))


def test_check_blocker_major_warns_exit_zero():
    proc = _run_check(str(FIXTURES / "mixed.txt"))
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "Review check: warn" in proc.stdout, (
        "warn check printed no warn verdict: %r" % (proc.stdout[:200],))
    assert "blocker=1" in proc.stdout and "major=1" in proc.stdout, (
        "warn check must report severity counts: %r" % (proc.stdout[:200],))


def test_check_malformed_reported_with_numbers():
    proc = _run_check(str(FIXTURES / "malformed.txt"))
    assert proc.returncode == 0, (
        "malformed check exited %d" % proc.returncode)
    assert "Review check: warn" in proc.stdout, (
        "malformed check printed no warn verdict: %r" % (proc.stdout[:200],))
    for lineno in ("L2:", "L3:", "L4:", "L6:"):
        assert lineno in proc.stdout, (
            "malformed check must report %s: %r" % (lineno, proc.stdout[:300]))
    assert "L1:" not in proc.stdout and "L5:" not in proc.stdout, (
        "well-shaped lines must not be flagged: %r" % (proc.stdout[:300],))


def test_check_block_mode_exit_two():
    env = _warn_env()
    env["REVIEW_PAIR_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "mixed.txt"), env=env)
    assert proc.returncode == 2, "block check exited %d, want 2" % (
        proc.returncode,)
    assert "Review check: warn" in proc.stdout, (
        "block check printed no warning")


def test_check_block_mode_clean_still_zero():
    env = _warn_env()
    env["REVIEW_PAIR_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "clean.txt"), env=env)
    assert proc.returncode == 0, "block check on clean input exited %d" % (
        proc.returncode,)
    assert "Review check: ok" in proc.stdout, (
        "block check on clean input printed no ok verdict")


def test_check_block_mode_malformed_only_exit_two():
    env = _warn_env()
    env["REVIEW_PAIR_MODE"] = "block"
    proc = _run_check(stdin_text="not a finding line at all\n", env=env)
    assert proc.returncode == 2, (
        "block check on malformed-only stdin exited %d, want 2"
        % proc.returncode,)
    assert "L1:" in proc.stdout, "block check must report the malformed line"


def test_check_stdin_findings():
    proc = _run_check(stdin_text=(
        "[RV-1] src/db.cs:12 blocker SQL string built from raw input here.\n"))
    assert proc.returncode == 0, "stdin check exited %d" % proc.returncode
    assert "Review check: warn" in proc.stdout, (
        "stdin blocker must warn: %r" % (proc.stdout[:200],))


def test_check_empty_file_fail_open():
    proc = _run_check(str(FIXTURES / "empty.txt"))
    assert proc.returncode == 0, "empty check exited %d" % proc.returncode
    assert proc.stdout == "", "empty check must print nothing on stdout"
    assert proc.stderr.strip(), "empty check must note fail-open on stderr"


def test_check_missing_file_fail_open():
    proc = _run_check(str(FIXTURES / "no-such-findings.txt"))
    assert proc.returncode == 0, "missing check exited %d" % proc.returncode
    assert proc.stdout == "", "missing check must print nothing on stdout"
    assert proc.stderr.strip(), "missing check must note fail-open on stderr"


def test_check_stdin_empty_fail_open():
    proc = _run_check(stdin_text="")
    assert proc.returncode == 0, (
        "empty-stdin check exited %d" % proc.returncode)
    assert proc.stdout == "", "empty-stdin check must print nothing on stdout"
    assert proc.stderr.strip(), (
        "empty-stdin check must note fail-open on stderr")


def test_check_block_mode_missing_input_still_zero():
    env = _warn_env()
    env["REVIEW_PAIR_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "no-such-findings.txt"), env=env)
    assert proc.returncode == 0, (
        "fail-open must stay exit 0 even in block mode, got %d"
        % proc.returncode,)
    assert proc.stderr.strip(), "block-mode fail-open must note on stderr"


def test_check_json_shape():
    proc = _run_check(str(FIXTURES / "mixed.txt"), "--json")
    assert proc.returncode == 0, "json check exited %d" % proc.returncode
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError("json check printed invalid JSON: %s" % exc)
    assert set(report) == {"findings", "malformed", "counts"}, (
        "json keys must be findings/malformed/counts, got %r"
        % (sorted(report),))
    assert report["counts"] == {
        "blocker": 1, "major": 1, "minor": 1, "nit": 1,
    }, "json counts wrong: %r" % (report.get("counts"),)
    assert report["malformed"] == [], "mixed fixture must have no malformed"
    assert len(report["findings"]) == 4, (
        "mixed fixture must parse 4 findings, got %d"
        % len(report["findings"]))
    first = report["findings"][0]
    assert first == {
        "id": "RV-1", "path": "src/db.cs", "line": 12,
        "severity": "blocker",
        "text": "SQL string built from raw input here.",
    }, "first finding parsed wrong: %r" % (first,)
    assert isinstance(first["line"], int), "finding line must be an int"

    bad = _run_check(str(FIXTURES / "malformed.txt"), "--json")
    assert bad.returncode == 0, "bad json check exited %d" % bad.returncode
    report = json.loads(bad.stdout)
    assert [entry["line"] for entry in report["malformed"]] == [2, 3, 4, 6], (
        "json malformed lines wrong: %r" % (report["malformed"],))
    assert report["counts"]["blocker"] == 1, (
        "malformed fixture keeps its valid blocker: %r" % (report["counts"],))


def test_check_json_fail_open():
    proc = _run_check(str(FIXTURES / "no-such-findings.txt"), "--json")
    assert proc.returncode == 0, "json fail-open exited %d" % proc.returncode
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError("json fail-open printed invalid JSON: %s" % exc)
    assert report["findings"] == [] and report["malformed"] == [], (
        "json fail-open must carry empty lists, got %r" % (report,))
    assert report["counts"] == {
        "blocker": 0, "major": 0, "minor": 0, "nit": 0,
    }, "json fail-open must carry zeroed counts, got %r" % (report,)
    assert proc.stderr.strip(), "json fail-open must still note on stderr"
