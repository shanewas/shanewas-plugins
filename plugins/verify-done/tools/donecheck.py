#!/usr/bin/env python3
"""verify-done: zero-dependency done-claim evidence gate (stdlib only).

Checks one done-claim text plus an optional files/commands log against
the three required evidence kinds:

    tools/donecheck.py check --claim CLAIM [--evidence LOG ...] [--json]

Every claim must reference build output, test output, and an artifact
or grep anchor. Matching is case-insensitive: build; test, pass,
green; artifact, anchor, ledger, screenshot. A kind the change
honestly needs can be waived with an `N/A:` line carrying a reason; a
bare `N/A:` with no reason waives nothing.

Warns and exits 0 when a kind is missing. With VERIFY_DONE_MODE=block
a tripped gate exits 2 instead. --claim and --evidence also resolve
from VERIFY_DONE_CLAIM and VERIFY_DONE_EVIDENCE. Missing or unreadable
inputs fail open: exit 0 with a stderr note, never a failure.

Works on Python 3.9+ with no third-party packages.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BLOCK_EXIT = 2

# Any word containing "build" is build-related (build, rebuild,
# prebuild), so the build pattern stays a loose substring. The rest
# anchor at a word or hyphen start so "latest" never cites test and
# "bypass" never cites pass.
BUILD_RES = (re.compile(r"\b\w*build\w*", re.IGNORECASE),)
TEST_RES = (
    re.compile(r"(?:\b|-)test(?:s|ed|ing)?\b", re.IGNORECASE),
    re.compile(r"(?:\b|-)(?:pass|passes|passed|passing)\b", re.IGNORECASE),
    re.compile(r"(?:\b|-)greens?\b", re.IGNORECASE),
)
ARTIFACT_RES = (
    re.compile(r"(?:\b|-)(?:artifact|anchor|ledger|screenshot)"
               r"(?:s|ed|ing)?\b", re.IGNORECASE),
)

KIND_PATTERNS = (
    ("build", BUILD_RES),
    ("test", TEST_RES),
    ("artifact", ARTIFACT_RES),
)


def kind_in(text, patterns):
    """True when any of the kind's patterns matches the text."""
    return any(pattern.search(text) for pattern in patterns)


def split_na(text):
    """Split body text into (plain_text, na_reasons).

    Only lines starting with `N/A:` (case-sensitive) count as waivers,
    and only when a non-empty reason follows the colon. Waiver lines
    stay out of the citation scan so `N/A: no tests` never cites test.
    """
    plain = []
    reasons = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("N/A:"):
            reason = stripped[len("N/A:"):].strip()
            if reason:
                reasons.append(reason)
        else:
            plain.append(line)
    return "\n".join(plain), reasons


def evaluate(claim_text, evidence_texts):
    """Return (cited, waived, missing) over claim plus evidence logs.

    cited maps each found kind to the source that named it first
    ("claim" wins over "evidence"). waived maps each waived kind to
    its N/A reason. missing lists the rest in canonical kind order.
    """
    sources = [("claim", claim_text)] + [
        ("evidence", text) for text in evidence_texts
    ]
    plain_by_source = {}
    reasons = []
    for source, text in sources:
        plain, found = split_na(text)
        plain_by_source.setdefault(source, []).append(plain)
        reasons.extend(found)
    cited = {}
    for kind, patterns in KIND_PATTERNS:
        for source in ("claim", "evidence"):
            combined = "\n".join(plain_by_source.get(source, []))
            if kind_in(combined, patterns):
                cited[kind] = source
                break
    waived = {}
    for reason in reasons:
        for kind, patterns in KIND_PATTERNS:
            if kind not in cited and kind not in waived \
                    and kind_in(reason, patterns):
                waived[kind] = reason
    missing = [kind for kind, _ in KIND_PATTERNS
               if kind not in cited and kind not in waived]
    return cited, waived, missing


def verdict_line(cited, waived, missing):
    """One-line human verdict shared by text and JSON output."""
    labels = dict(
        (kind, "%s N/A" % kind if kind in waived else kind)
        for kind, _ in KIND_PATTERNS
    )
    if not missing:
        return "Done check: ok - all evidence kinds present (%s)" % (
            ", ".join(labels[kind] for kind, _ in KIND_PATTERNS))
    have = [labels[kind] for kind, _ in KIND_PATTERNS
            if kind not in missing]
    return "Done check: warn - missing evidence kinds: %s (have: %s)" % (
        ", ".join(missing), ", ".join(have) if have else "none")


def read_input(path):
    """Return (text, error) for an input path. error is "" on success."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace"), ""
    except OSError as exc:
        return None, "%s: %s" % (path, exc)


def fail_open(args, reason, mode, claim_path, evidence_paths):
    """Missing or unreadable inputs: stderr note, exit 0, never a failure."""
    print("verify-done: %s" % reason, file=sys.stderr)
    if args.json:
        print(json.dumps({
            "ok": True,
            "missing": [],
            "cited": [],
            "waived": {},
            "mode": "block" if mode == "block" else "warn",
            "claim": claim_path,
            "evidence": evidence_paths,
            "note": reason,
        }, indent=2, ensure_ascii=False))
    return 0


def cmd_check(args) -> int:
    mode = os.environ.get("VERIFY_DONE_MODE", "")
    claim_path = args.claim or os.environ.get("VERIFY_DONE_CLAIM", "").strip()
    evidence_paths = list(args.evidence or [])
    env_evidence = os.environ.get("VERIFY_DONE_EVIDENCE", "").strip()
    if env_evidence and not evidence_paths:
        evidence_paths.append(env_evidence)
    if not claim_path:
        return fail_open(args, "no --claim given (set VERIFY_DONE_CLAIM)",
                         mode, "", evidence_paths)
    claim_text, error = read_input(claim_path)
    if claim_text is None:
        return fail_open(args, "cannot read claim file %s" % error,
                         mode, claim_path, evidence_paths)
    evidence_texts = []
    for log in evidence_paths:
        text, error = read_input(log)
        if text is None:
            return fail_open(args, "cannot read evidence file %s" % error,
                             mode, claim_path, evidence_paths)
        evidence_texts.append(text)
    cited, waived, missing = evaluate(claim_text, evidence_texts)
    line = verdict_line(cited, waived, missing)
    if args.json:
        print(json.dumps({
            "ok": not missing,
            "missing": missing,
            "cited": [kind for kind, _ in KIND_PATTERNS if kind in cited],
            "waived": dict((kind, waived[kind]) for kind, _ in KIND_PATTERNS
                           if kind in waived),
            "mode": "block" if mode == "block" else "warn",
            "claim": claim_path,
            "evidence": evidence_paths,
            "systemMessage": line,
        }, indent=2, ensure_ascii=False))
    else:
        print(line)
    if missing and mode == "block":
        return BLOCK_EXIT
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="donecheck.py",
        description="Check a done claim against required build, test, "
                    "and artifact evidence.")
    sub = ap.add_subparsers(dest="command", required=True)

    ch = sub.add_parser("check", help="warn (or block) on missing evidence")
    ch.add_argument("--claim", metavar="CLAIM",
                    help="done-claim file; else $VERIFY_DONE_CLAIM")
    ch.add_argument("--evidence", metavar="LOG", action="append", default=[],
                    help="files/commands log; repeatable, "
                         "else $VERIFY_DONE_EVIDENCE")
    ch.add_argument("--json", action="store_true",
                    help="machine-readable verdict")
    ch.set_defaults(func=cmd_check)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
