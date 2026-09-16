"""minimal-diff check tests: silent-vs-warn exits plus fail-open input."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

DIFFGATE = ROOT / "plugins" / "minimal-diff" / "tools" / "diffgate.py"
FIXTURES = ROOT / "tests" / "fixtures" / "diff"


def _warn_env():
    env = dict(os.environ)
    env.pop("DIFF_GATE_MODE", None)
    env.pop("DIFF_GATE_MAX_FILES", None)
    env.pop("DIFF_GATE_MAX_LINES", None)
    env.pop("DIFF_GATE_MAX_CONCERNS", None)
    return env


def _run_check(*args, env=None, stdin_text=None):
    return subprocess.run(
        [sys.executable, str(DIFFGATE), "check", *args],
        capture_output=True, text=True, timeout=60,
        env=_warn_env() if env is None else env, input=stdin_text)


def _file_hunk(path, added=1, removed=0):
    lines = ["diff --git a/%s b/%s" % (path, path),
             "--- a/%s" % path, "+++ b/%s" % path,
             "@@ -1,%d +1,%d @@" % (removed + 1, added + 1),
             " context"]
    lines += ["+added %d" % i for i in range(added)]
    lines += ["-removed %d" % i for i in range(removed)]
    return "\n".join(lines) + "\n"


def test_check_small_diff_silent():
    proc = _run_check(str(FIXTURES / "small.diff"))
    assert proc.returncode == 0, "small check exited %d" % proc.returncode
    assert proc.stdout == "", "small check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_small_diff_stdin_silent():
    text = (FIXTURES / "small.diff").read_text(encoding="utf-8")
    proc = _run_check(stdin_text=text)
    assert proc.returncode == 0, "stdin check exited %d" % proc.returncode
    assert proc.stdout == "", "stdin small check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_large_diff_warns_exit_zero():
    proc = _run_check(str(FIXTURES / "large.diff"))
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "Diff gate" in proc.stdout, "warn check printed no warning: %r" % (
        proc.stdout[:200],)
    assert "files=7" in proc.stdout, "warning lacks file count: %r" % (
        proc.stdout[:200],)


def test_check_many_lines_warns():
    proc = _run_check(stdin_text=_file_hunk("src/big.py", added=500))
    assert proc.returncode == 0, "lines check exited %d" % proc.returncode
    assert "Diff gate" in proc.stdout, "lines check printed no warning: %r" % (
        proc.stdout[:200],)
    assert "lines=+500/-0" in proc.stdout, "warning lacks line count: %r" % (
        proc.stdout[:200],)


def test_check_concerns_warns():
    # max(dirs, exts) scores concerns.diff 3 (silent), so the trip-case moved here.
    proc = _run_check(str(FIXTURES / "many-concerns.diff"))
    assert proc.returncode == 0, "concerns check exited %d" % proc.returncode
    assert "Diff gate" in proc.stdout, (
        "concerns check printed no warning: %r" % (proc.stdout[:200],))
    assert "concerns=4" in proc.stdout, "warning lacks concern count: %r" % (
        proc.stdout[:200],)


def test_single_idea_mixed_types_passes():
    # max(dirs, exts) scores 2 dirs + 2 exts as 2, not 4: no trip.
    proc = _run_check(str(FIXTURES / "mixed-single-idea.diff"))
    assert proc.returncode == 0, "mixed check exited %d" % proc.returncode
    assert proc.stdout == "", "single-idea mixed-type diff must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_boundary_limits_silent():
    diff = "".join(_file_hunk("src/f%d.py" % i) for i in range(5))
    proc = _run_check(stdin_text=diff)
    assert proc.returncode == 0, "boundary check exited %d" % proc.returncode
    assert proc.stdout == "", "exactly-at-limit diff must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_block_mode_exit_two():
    env = _warn_env()
    env["DIFF_GATE_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "large.diff"), env=env)
    assert proc.returncode == 2, "block check exited %d, want 2" % proc.returncode
    assert "Diff gate" in proc.stdout, "block check printed no warning"


def test_check_block_mode_clean_still_zero():
    env = _warn_env()
    env["DIFF_GATE_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "small.diff"), env=env)
    assert proc.returncode == 0, "block check on small diff exited %d" % (
        proc.returncode,)
    assert proc.stdout == "", "clean block check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_unparseable_fail_open():
    proc = _run_check(str(FIXTURES / "garbage.txt"))
    assert proc.returncode == 0, "garbage check exited %d" % proc.returncode
    assert proc.stdout == "", "garbage check must warn nowhere on stdout"
    assert proc.stderr.strip(), "garbage check must note fail-open on stderr"


def test_check_empty_stdin_silent():
    proc = _run_check(stdin_text="")
    assert proc.returncode == 0, "empty stdin check exited %d" % proc.returncode
    assert proc.stdout == "", "empty stdin check must stay silent"


def test_check_missing_file_silent():
    proc = _run_check(str(FIXTURES / "no-such-diff.diff"))
    assert proc.returncode == 0, "missing file check exited %d" % proc.returncode
    assert proc.stdout == "", "missing file check must stay silent"


def test_check_flag_overrides_honored():
    loud = _run_check(str(FIXTURES / "large.diff"), "--max-files", "7")
    assert loud.returncode == 0 and loud.stdout == "", (
        "7 files must pass --max-files 7, got %r" % loud.stdout[:200])
    quiet = _run_check(str(FIXTURES / "small.diff"), "--max-lines", "1")
    assert quiet.returncode == 0 and "Diff gate" in quiet.stdout, (
        "2 lines must trip --max-lines 1")


def test_check_env_overrides_honored():
    env = _warn_env()
    env["DIFF_GATE_MAX_FILES"] = "10"
    proc = _run_check(str(FIXTURES / "large.diff"), env=env)
    assert proc.returncode == 0 and proc.stdout == "", (
        "7 files must pass DIFF_GATE_MAX_FILES=10, got %r" % proc.stdout[:200])
    env["DIFF_GATE_MAX_CONCERNS"] = "1"
    proc = _run_check(str(FIXTURES / "small.diff"), env=env)
    # max(dirs, exts) scores small.diff 2 (was 3); still trips a max of 1.
    assert "Diff gate" in proc.stdout, (
        "concerns 2 must trip DIFF_GATE_MAX_CONCERNS=1")


HOOK_KEYS = {"systemMessage", "decision", "reason",
             "hookSpecificOutput", "suppressOutput"}


def test_hook_output_strict_keys():
    proc = _run_check(str(FIXTURES / "many-concerns.diff"), "--hook")
    assert proc.returncode == 0, "hook check exited %d" % proc.returncode
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError("hook output is not JSON: %s" % exc)
    assert set(report) <= HOOK_KEYS, "hook keys %r not hook-safe" % (
        sorted(set(report)),)
    assert report.get("systemMessage"), "hook output lacks systemMessage"
    assert "decision" not in report, "warn-mode hook must not block"


def test_hook_block_mode_decision():
    env = _warn_env()
    env["DIFF_GATE_MODE"] = "block"
    proc = _run_check(str(FIXTURES / "many-concerns.diff"), "--hook", env=env)
    assert proc.returncode == 0, "hook block must exit 0, got %d" % (
        proc.returncode,)
    report = json.loads(proc.stdout)
    assert report.get("decision") == "block", "hook block lacks decision"
    assert report.get("reason"), "hook block lacks reason"
    assert report.get("systemMessage"), "hook block lacks systemMessage"
