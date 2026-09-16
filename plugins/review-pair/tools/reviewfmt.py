#!/usr/bin/env python3
"""review-pair: zero-dependency review-findings shape gate (stdlib only).

Reads review findings text, one finding per line, and validates the
machine-readable shape:

    tools/reviewfmt.py check [FILE] [--json]

With no FILE, `check` reads findings from stdin, so it slots behind
any review step that prints findings. Each line must match:

    [ID-1] path/to/file.cs:42 severity finding text here

where severity is blocker, major, minor, or nit and the text runs at
least 10 characters. The gate reports counts per severity plus any
malformed lines with their line numbers.

Warns and exits 0 when any finding is blocker/major or any line is
malformed. With REVIEW_PAIR_MODE=block a tripped gate exits 2
instead. Missing, unreadable, or empty input fails open: exit 0 with
a stderr note, never a failure. --json emits the parsed findings for
piping into an audit ledger.

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

FINDING_RE = re.compile(
    r"^\[([A-Z]+-\d+)\] (\S+):(\d+) (blocker|major|minor|nit) (.{10,})$"
)

SEVERITIES = ("blocker", "major", "minor", "nit")


def empty_counts():
    """Fresh zeroed per-severity counts. One shape everywhere."""
    return dict((severity, 0) for severity in SEVERITIES)


def parse_findings(text):
    """Split findings text into (findings, malformed).

    Blank lines are skipped, so a trailing newline never counts as a
    malformed finding. malformed entries carry the 1-based input line
    number plus the raw line.
    """
    findings = []
    malformed = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        match = FINDING_RE.match(line)
        if match:
            findings.append({
                "id": match.group(1),
                "path": match.group(2),
                "line": int(match.group(3)),
                "severity": match.group(4),
                "text": match.group(5),
            })
        else:
            malformed.append({"line": lineno, "text": raw.strip()})
    return findings, malformed


def count_by_severity(findings):
    counts = empty_counts()
    for finding in findings:
        counts[finding["severity"]] += 1
    return counts


def tripped(counts, malformed):
    """Blockers, majors, and malformed lines all trip the gate."""
    return (counts["blocker"] > 0 or counts["major"] > 0
            or len(malformed) > 0)


def verdict_lines(findings, malformed, counts):
    """Human verdict plus one line per malformed input line."""
    head = "Review check: %s - %d findings " % (
        "warn" if tripped(counts, malformed) else "ok", len(findings))
    head += "(%s)" % ", ".join("%s=%d" % (severity, counts[severity])
                               for severity in SEVERITIES)
    if malformed:
        head += ", %d malformed" % len(malformed)
    lines = [head]
    for bad in malformed:
        lines.append("  L%d: '%s'" % (bad["line"], bad["text"]))
    return lines


def report_payload(findings, malformed, counts):
    """JSON shape for piping into an audit ledger. Stable keys."""
    return {
        "findings": findings,
        "malformed": malformed,
        "counts": counts,
    }


def read_input(path):
    """Return (text, error) for a findings file or stdin. error is "" ok."""
    if path is None:
        try:
            return sys.stdin.read(), ""
        except OSError as exc:
            return None, "stdin: %s" % exc
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace"), ""
    except OSError as exc:
        return None, "%s: %s" % (path, exc)


def fail_open(args, reason):
    """Missing, unreadable, or empty input: stderr note, exit 0."""
    print("review-pair: %s" % reason, file=sys.stderr)
    if args.json:
        print(json.dumps(report_payload([], [], empty_counts()),
                         indent=2, ensure_ascii=False))
    return 0


def cmd_check(args) -> int:
    text, error = read_input(args.file)
    if text is None:
        return fail_open(args, "cannot read findings input %s" % error)
    if not text.strip():
        return fail_open(args, "no findings to check (empty input)")
    findings, malformed = parse_findings(text)
    counts = count_by_severity(findings)
    if args.json:
        print(json.dumps(report_payload(findings, malformed, counts),
                         indent=2, ensure_ascii=False))
    else:
        print("\n".join(verdict_lines(findings, malformed, counts)))
    if tripped(counts, malformed) \
            and os.environ.get("REVIEW_PAIR_MODE") == "block":
        return BLOCK_EXIT
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="reviewfmt.py",
        description="Validate review findings shape: one machine-readable "
                    "finding per line.")
    sub = ap.add_subparsers(dest="command", required=True)

    ch = sub.add_parser("check",
                        help="warn (or block) on blocker/major findings "
                             "and malformed lines")
    ch.add_argument("file", nargs="?",
                    help="findings file to check; omit to read from stdin")
    ch.add_argument("--json", action="store_true",
                    help="machine-readable findings for an audit ledger")
    ch.set_defaults(func=cmd_check)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
