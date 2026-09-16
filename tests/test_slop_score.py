"""slop-gate score tests: exact threshold boundaries plus fixture pins.

Bands are <20 clean, 20-40 marginal, 40-60 heavy, >60 severe. The
boundary fixtures carry exact hit counts (weight 10 each, no rhythm
signal), so their scores must equal 20, 40, and 60 precisely.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontmatter import ROOT

SLOP = ROOT / "plugins" / "slop-gate" / "tools" / "slop.py"
FIXTURES = ROOT / "tests" / "fixtures" / "slop"


def _load_slop():
    spec = importlib.util.spec_from_file_location("slop", SLOP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _score_json(name):
    proc = subprocess.run(
        [sys.executable, str(SLOP), "score", str(FIXTURES / name),
         "--json", "--no-profile"],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, "score %s exited %d: %s" % (
        name, proc.returncode, proc.stderr)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError("score %s printed invalid JSON: %r" % (
            name, proc.stdout[:200]))


def test_band_boundaries_exact():
    slop = _load_slop()
    cases = [(0, "clean"), (19, "clean"), (20, "marginal"), (39, "marginal"),
             (40, "heavy"), (59, "heavy"), (60, "severe"), (100, "severe")]
    for score, want in cases:
        got = slop.band_for_score(score)
        assert got == want, "band_for_score(%d) = %r, want %r" % (
            score, got, want)


def test_fixture_scores_exact_20():
    report = _score_json("boundary-20.md")
    assert report["score"] == 20, "boundary-20.md scored %r, want 20" % (
        report["score"],)
    assert report["band"] == "marginal", "boundary-20.md band %r" % report["band"]


def test_fixture_scores_exact_40():
    report = _score_json("boundary-40.md")
    assert report["score"] == 40, "boundary-40.md scored %r, want 40" % (
        report["score"],)
    assert report["band"] == "heavy", "boundary-40.md band %r" % report["band"]


def test_fixture_scores_exact_60():
    report = _score_json("boundary-60.md")
    assert report["score"] == 60, "boundary-60.md scored %r, want 60" % (
        report["score"],)
    assert report["band"] == "severe", "boundary-60.md band %r" % report["band"]


def test_clean_fixture_under_threshold():
    report = _score_json("clean.md")
    assert report["score"] < 20, "clean.md scored %d, want <20" % report["score"]
    assert report["band"] == "clean", "clean.md band %r" % report["band"]


def test_sloppy_fixture_trips_gate():
    report = _score_json("sloppy.md")
    assert report["score"] >= 40, "sloppy.md scored %d, want >=40" % (
        report["score"],)
