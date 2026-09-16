"""commit-gate check tests: message shape, trailers, staged bans, exits."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

COMMITCHECK = ROOT / "plugins" / "commit-gate" / "tools" / "commitcheck.py"
FIXTURES = ROOT / "tests" / "fixtures" / "commit"


def _warn_env():
    env = dict(os.environ)
    env.pop("COMMIT_GATE_MODE", None)
    env.pop("COMMIT_GATE_BAN", None)
    env.pop("COMMIT_GATE_ALLOW", None)
    return env


def _run_check(*args, env=None):
    return subprocess.run(
        [sys.executable, str(COMMITCHECK), "check", *args],
        capture_output=True, text=True, timeout=60,
        env=_warn_env() if env is None else env)


def test_check_good_message_passes_silent():
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "good check exited %d: %s" % (
        proc.returncode, proc.stderr[:200])
    assert proc.stdout == "", "good check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_long_subject_warns():
    proc = _run_check("--message-file", str(FIXTURES / "long-subject.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "Commit gate" in proc.stdout, "long subject printed no warning"
    assert "50" in proc.stdout, "warning lacks the 50-char limit: %r" % (
        proc.stdout[:200],)


def test_check_bad_shape_warns():
    proc = _run_check("--message-file", str(FIXTURES / "bad-shape.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "Conventional" in proc.stdout, (
        "bad shape warning missing: %r" % proc.stdout[:200])


def test_check_ai_trailer_caught():
    proc = _run_check("--message-file", str(FIXTURES / "ai-trailer.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "AI trailer" in proc.stdout, "co-authored bot line not caught: %r" % (
        proc.stdout[:200],)


def test_check_generated_trailer_caught():
    proc = _run_check("--message-file", str(FIXTURES / "generated.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "AI trailer" in proc.stdout, "generated-by bot line not caught: %r" % (
        proc.stdout[:200],)


def test_check_banned_extension_caught():
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "src/app.py\nbuild/report.xlsx")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "banned" in proc.stdout, "xlsx staged file not caught: %r" % (
        proc.stdout[:200],)


def test_check_md_json_allowed_by_default():
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "docs/notes.md\ndata/blob.json")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert proc.stdout == "", "md/json must pass by default, got %r" % (
        proc.stdout[:200],)


def test_check_allow_override():
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "build/report.xlsx", "--allow", "xlsx")
    assert proc.returncode == 0, "allow check exited %d" % proc.returncode
    assert proc.stdout == "", "--allow xlsx must unban xlsx, got %r" % (
        proc.stdout[:200],)


def test_check_ban_flag_adds_extension():
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "docs/notes.md", "--ban", "md")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "banned" in proc.stdout, "--ban md must trip on .md: %r" % (
        proc.stdout[:200],)


def test_check_staged_at_file_form():
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "@%s" % (FIXTURES / "staged.txt",))
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "report.xlsx" in proc.stdout, "@file staged list not read: %r" % (
        proc.stdout[:200],)


def test_check_block_mode_exits_two():
    env = _warn_env()
    env["COMMIT_GATE_MODE"] = "block"
    proc = _run_check("--message-file", str(FIXTURES / "bad-shape.txt"),
                      "--staged", "src/app.py", env=env)
    assert proc.returncode == 2, "block check exited %d, want 2" % proc.returncode
    assert "Commit gate" in proc.stdout, "block check printed no warning"


def test_check_block_mode_clean_still_zero():
    env = _warn_env()
    env["COMMIT_GATE_MODE"] = "block"
    proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "src/app.py", env=env)
    assert proc.returncode == 0, "block check on clean input exited %d" % (
        proc.returncode,)
    assert proc.stdout == "", "clean block check must stay silent, got %r" % (
        proc.stdout[:200],)


def test_check_missing_message_file_fails_open():
    proc = _run_check("--staged", "src/app.py")
    assert proc.returncode == 0, "missing input check exited %d" % proc.returncode
    assert proc.stdout == "", "fail-open must print no warning, got %r" % (
        proc.stdout[:200],)
    assert "commit-gate" in proc.stderr, "fail-open printed no stderr note"


def test_check_unreadable_message_file_fails_open():
    proc = _run_check("--message-file", str(FIXTURES / "no-such-file.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "unreadable input check exited %d" % (
        proc.returncode,)
    assert proc.stdout == "", "fail-open must print no warning"
    assert "commit-gate" in proc.stderr, "fail-open printed no stderr note"


def test_check_git_unavailable_fails_open():
    with tempfile.TemporaryDirectory(prefix="commit-gate-") as tmp:
        env = _warn_env()
        env["PATH"] = tmp
        proc = _run_check("--message-file", str(FIXTURES / "good.txt"),
                          env=env)
    assert proc.returncode == 0, "no-git check exited %d" % proc.returncode
    assert proc.stdout == "", "no-git fail-open must print no warning"
    assert "git" in proc.stderr.lower(), (
        "no-git fail-open printed no git note: %r" % proc.stderr[:200])


def test_check_json_shape():
    proc = _run_check("--message-file", str(FIXTURES / "bad-shape.txt"),
                      "--staged", "src/app.py", "--json")
    assert proc.returncode == 0, "json check exited %d" % proc.returncode
    report = json.loads(proc.stdout)
    for key in ("ok", "violations", "mode", "message", "staged",
                "systemMessage"):
        assert key in report, "json report lacks %r: %r" % (key, report)
    assert report["ok"] is False, "bad shape must report ok:false"
    assert report["violations"], "bad shape must list violations"
    assert report["mode"] == "warn", "default mode must be warn"


def test_check_json_fail_open_shape():
    proc = _run_check("--message-file", str(FIXTURES / "no-such-file.txt"),
                      "--staged", "src/app.py", "--json")
    assert proc.returncode == 0, "json fail-open exited %d" % proc.returncode
    report = json.loads(proc.stdout)
    assert report["ok"] is True, "fail-open must report ok:true"
    assert report["note"], "fail-open json must carry the note"


def test_check_ticket_regex():
    hit = _run_check("--message-file", str(FIXTURES / "ticket.txt"),
                     "--staged", "src/app.py",
                     "--ticket-regex", r"PROJ-\d+")
    assert hit.returncode == 0 and hit.stdout == "", (
        "ticket ref must pass, got %r" % hit.stdout[:200])
    miss = _run_check("--message-file", str(FIXTURES / "good.txt"),
                      "--staged", "src/app.py",
                      "--ticket-regex", r"PROJ-\d+")
    assert miss.returncode == 0 and "ticket" in miss.stdout.lower(), (
        "missing ticket ref must warn, got %r" % miss.stdout[:200])


def test_check_comments_only_is_empty():
    proc = _run_check("--message-file", str(FIXTURES / "comments-only.txt"),
                      "--staged", "src/app.py")
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "empty commit message" in proc.stdout, (
        "comments-only file must warn as empty: %r" % proc.stdout[:200])


HOOK_KEYS = {"systemMessage", "decision", "reason",
             "hookSpecificOutput", "suppressOutput"}


def test_hook_output_strict_keys():
    proc = _run_check("--message-file", str(FIXTURES / "bad-shape.txt"),
                      "--staged", "src/app.py", "--hook")
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
    env["COMMIT_GATE_MODE"] = "block"
    proc = _run_check("--message-file", str(FIXTURES / "bad-shape.txt"),
                      "--staged", "src/app.py", "--hook", env=env)
    assert proc.returncode == 0, "hook block must exit 0, got %d" % (
        proc.returncode,)
    report = json.loads(proc.stdout)
    assert report.get("decision") == "block", "hook block lacks decision"
    assert report.get("reason"), "hook block lacks reason"
    assert report.get("systemMessage"), "hook block lacks systemMessage"
