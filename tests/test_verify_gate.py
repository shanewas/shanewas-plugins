"""verify-done check tests: ok-vs-warn exits, N/A waivers, fail-open input."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

DONECHECK = ROOT / "plugins" / "verify-done" / "tools" / "donecheck.py"
FIXTURES = ROOT / "tests" / "fixtures" / "verify"


def _warn_env():
    env = dict(os.environ)
    env.pop("VERIFY_DONE_MODE", None)
    env.pop("VERIFY_DONE_CLAIM", None)
    env.pop("VERIFY_DONE_EVIDENCE", None)
    return env


def _run_check(*args, env=None):
    return subprocess.run(
        [sys.executable, str(DONECHECK), "check", *args],
        capture_output=True, text=True, timeout=60,
        env=_warn_env() if env is None else env)


def test_check_complete_claim_passes():
    proc = _run_check("--claim", str(FIXTURES / "good-claim.txt"))
    assert proc.returncode == 0, "good check exited %d" % proc.returncode
    assert "Done check: ok" in proc.stdout, (
        "good check printed no ok verdict: %r" % (proc.stdout[:200],))


def test_check_missing_test_warns_exit_zero():
    proc = _run_check("--claim", str(FIXTURES / "bad-claim.txt"))
    assert proc.returncode == 0, "warn check exited %d" % proc.returncode
    assert "Done check: warn" in proc.stdout, (
        "warn check printed no warn verdict: %r" % (proc.stdout[:200],))
    assert "test" in proc.stdout, (
        "warn check must name the missing kind: %r" % (proc.stdout[:200],))


def test_check_block_mode_exit_two():
    env = _warn_env()
    env["VERIFY_DONE_MODE"] = "block"
    proc = _run_check("--claim", str(FIXTURES / "bad-claim.txt"), env=env)
    assert proc.returncode == 2, "block check exited %d, want 2" % (
        proc.returncode,)
    assert "Done check: warn" in proc.stdout, "block check printed no warning"


def test_check_block_mode_complete_still_zero():
    env = _warn_env()
    env["VERIFY_DONE_MODE"] = "block"
    proc = _run_check("--claim", str(FIXTURES / "good-claim.txt"), env=env)
    assert proc.returncode == 0, "block check on good claim exited %d" % (
        proc.returncode,)
    assert "Done check: ok" in proc.stdout, (
        "block check on good claim printed no ok verdict")


def test_check_na_with_reason_accepted():
    proc = _run_check("--claim", str(FIXTURES / "na-claim.txt"))
    assert proc.returncode == 0, "N/A check exited %d" % proc.returncode
    assert "Done check: ok" in proc.stdout, (
        "N/A-with-reason claim must pass: %r" % (proc.stdout[:200],))
    assert "test N/A" in proc.stdout, (
        "ok verdict must mark the waived kind: %r" % (proc.stdout[:200],))


def test_check_bare_na_not_accepted():
    proc = _run_check("--claim", str(FIXTURES / "bare-na-claim.txt"))
    assert proc.returncode == 0, "bare-N/A check exited %d" % proc.returncode
    assert "Done check: warn" in proc.stdout, (
        "bare N/A: must not waive: %r" % (proc.stdout[:200],))
    assert "test" in proc.stdout, "bare-N/A warning must name test as missing"


def test_check_evidence_contributes():
    proc = _run_check("--claim", str(FIXTURES / "bad-claim.txt"),
                      "--evidence", str(FIXTURES / "evidence.log"))
    assert proc.returncode == 0, "evidence check exited %d" % proc.returncode
    assert "Done check: ok" in proc.stdout, (
        "evidence log citing tests must complete the claim: %r"
        % (proc.stdout[:200],))


def test_check_missing_claim_fail_open():
    proc = _run_check("--claim", str(FIXTURES / "no-such-claim.txt"))
    assert proc.returncode == 0, "missing claim check exited %d" % (
        proc.returncode,)
    assert proc.stdout == "", "missing claim check must print nothing on stdout"
    assert proc.stderr.strip(), "missing claim check must note fail-open on stderr"


def test_check_missing_evidence_fail_open():
    proc = _run_check("--claim", str(FIXTURES / "good-claim.txt"),
                      "--evidence", str(FIXTURES / "no-such-evidence.log"))
    assert proc.returncode == 0, "missing evidence check exited %d" % (
        proc.returncode,)
    assert proc.stdout == "", (
        "missing evidence check must print nothing on stdout")
    assert proc.stderr.strip(), (
        "missing evidence check must note fail-open on stderr")


def test_check_no_claim_fail_open():
    proc = _run_check()
    assert proc.returncode == 0, "no-claim check exited %d" % proc.returncode
    assert proc.stdout == "", "no-claim check must print nothing on stdout"
    assert proc.stderr.strip(), "no-claim check must note fail-open on stderr"


def test_check_block_mode_missing_input_still_zero():
    env = _warn_env()
    env["VERIFY_DONE_MODE"] = "block"
    proc = _run_check("--claim", str(FIXTURES / "no-such-claim.txt"), env=env)
    assert proc.returncode == 0, (
        "fail-open must stay exit 0 even in block mode, got %d"
        % proc.returncode,)
    assert proc.stderr.strip(), "block-mode fail-open must note on stderr"


def test_check_env_claim_fallback():
    env = _warn_env()
    env["VERIFY_DONE_CLAIM"] = str(FIXTURES / "good-claim.txt")
    proc = _run_check(env=env)
    assert proc.returncode == 0, "env claim check exited %d" % proc.returncode
    assert "Done check: ok" in proc.stdout, (
        "VERIFY_DONE_CLAIM must resolve the claim: %r" % (proc.stdout[:200],))


def test_check_json_shape():
    proc = _run_check("--claim", str(FIXTURES / "bad-claim.txt"), "--json")
    assert proc.returncode == 0, "json check exited %d" % proc.returncode
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError("json check printed invalid JSON: %s" % exc)
    assert report["ok"] is False, "bad claim json must carry ok:false"
    assert report["missing"] == ["test"], (
        "bad claim json missing must be [\"test\"], got %r"
        % (report.get("missing"),))
    assert report["cited"] == ["build", "artifact"], (
        "bad claim json cited wrong: %r" % (report.get("cited"),))
    assert isinstance(report["waived"], dict), "json waived must be an object"
    assert report["systemMessage"], "json must carry a systemMessage verdict"
    assert report["mode"] == "warn", "json mode must be warn by default"

    good = _run_check("--claim", str(FIXTURES / "good-claim.txt"), "--json")
    assert good.returncode == 0, "good json check exited %d" % good.returncode
    report = json.loads(good.stdout)
    assert report["ok"] is True and report["missing"] == [], (
        "good claim json must carry ok:true with no missing, got %r"
        % (report,))


def test_check_json_fail_open():
    proc = _run_check("--claim", str(FIXTURES / "no-such-claim.txt"), "--json")
    assert proc.returncode == 0, "json fail-open exited %d" % proc.returncode
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError("json fail-open printed invalid JSON: %s" % exc)
    assert report["ok"] is True, "json fail-open must carry ok:true"
    assert report.get("note"), "json fail-open must carry a note"
    assert proc.stderr.strip(), "json fail-open must still note on stderr"


HOOK_KEYS = {"systemMessage", "decision", "reason",
             "hookSpecificOutput", "suppressOutput"}


def test_hook_output_strict_keys():
    proc = _run_check("--claim", str(FIXTURES / "bad-claim.txt"), "--hook")
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
    env["VERIFY_DONE_MODE"] = "block"
    proc = _run_check("--claim", str(FIXTURES / "bad-claim.txt"), "--hook",
                      env=env)
    assert proc.returncode == 0, "hook block must exit 0, got %d" % (
        proc.returncode,)
    report = json.loads(proc.stdout)
    assert report.get("decision") == "block", "hook block lacks decision"
    assert report.get("reason"), "hook block lacks reason"
    assert report.get("systemMessage"), "hook block lacks systemMessage"
