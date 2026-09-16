"""slop-gate check/learn tests: warn-vs-block exits plus hook input."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

SLOP = ROOT / "plugins" / "slop-gate" / "tools" / "slop.py"
FIXTURES = ROOT / "tests" / "fixtures" / "slop"


def _warn_env():
    env = dict(os.environ)
    env.pop("SLOP_GATE_MODE", None)
    return env


def _run_check(*args, env=None, stdin_text=None):
    return subprocess.run(
        [sys.executable, str(SLOP), "check", "--no-profile", *args],
        capture_output=True, text=True, timeout=60,
        env=_warn_env() if env is None else env, input=stdin_text)


def test_check_warn_default_exit_zero():
    proc = _run_check(str(FIXTURES / "sloppy.md"))
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "Slop gate" in proc.stdout, "warn check printed no warning: %r" % (
        proc.stdout[:200],)
    assert "score=" in proc.stdout, "warning lacks score: %r" % proc.stdout[:200]


def test_check_block_mode_exit_two():
    env = _warn_env()
    env["SLOP_GATE_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "sloppy.md"), env=env)
    assert proc.returncode == 2, "block check exited %d, want 2" % proc.returncode
    assert "Slop gate" in proc.stdout, "block check printed no warning"


def test_check_block_mode_clean_still_zero():
    env = _warn_env()
    env["SLOP_GATE_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "clean.md"), env=env)
    assert proc.returncode == 0, "block check on clean file exited %d" % (
        proc.returncode,)
    assert proc.stdout == "", "clean check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_clean_silent():
    proc = _run_check(str(FIXTURES / "clean.md"))
    assert proc.returncode == 0, "clean check exited %d" % proc.returncode
    assert proc.stdout == "", "clean check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_threshold_flag():
    loud = _run_check(str(FIXTURES / "boundary-20.md"), "--threshold", "20")
    assert loud.returncode == 0 and "Slop gate" in loud.stdout, (
        "score 20 must trip threshold 20")
    quiet = _run_check(str(FIXTURES / "boundary-20.md"), "--threshold", "21")
    assert quiet.returncode == 0 and quiet.stdout == "", (
        "score 20 must not trip threshold 21, got %r" % quiet.stdout[:200])


def test_check_missing_file_silent():
    proc = _run_check(str(FIXTURES / "no-such-file.md"))
    assert proc.returncode == 0, "missing file check exited %d" % proc.returncode
    assert proc.stdout == "", "missing file check must stay silent"


def test_check_stdin_hook_event():
    event = json.dumps({"tool_input": {"file_path": str(FIXTURES / "sloppy.md")}})
    proc = _run_check(stdin_text=event)
    assert proc.returncode == 0, "stdin check exited %d" % proc.returncode
    assert "Slop gate" in proc.stdout, "stdin check printed no warning: %r" % (
        proc.stdout[:200],)


def test_check_stdin_empty_silent():
    proc = _run_check(stdin_text="")
    assert proc.returncode == 0, "empty stdin check exited %d" % proc.returncode
    assert proc.stdout == "", "empty stdin check must stay silent"


def test_learn_writes_profile():
    with tempfile.TemporaryDirectory(prefix="slop-gate-") as tmp:
        out = str(Path(tmp) / "voice-profile.json")
        proc = subprocess.run(
            [sys.executable, str(SLOP), "learn", str(FIXTURES / "clean.md"),
             "--profile", out],
            capture_output=True, text=True, timeout=60, env=_warn_env())
        assert proc.returncode == 0, "learn exited %d: %s" % (
            proc.returncode, proc.stderr[:200])
        payload = json.loads(Path(out).read_text(encoding="utf-8"))
        assert payload["samples"] == 1, "learn samples %r" % payload.get("samples")
        assert "burstiness" in payload["profile"], "profile lacks metrics"
