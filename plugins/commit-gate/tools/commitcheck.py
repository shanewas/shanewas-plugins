#!/usr/bin/env python3
"""commit-gate: zero-dependency commit-message and staged-file gate (stdlib only).

    tools/commitcheck.py check --message-file MSG [--staged PATHS] [--json]

Reads one commit message plus the staged file list and reports every
violation it finds:

- subject line over 50 chars
- body line over 72 chars
- subject outside Conventional Commits shape
  (type[(scope)][!]: description)
- AI trailer lines (Co-authored-by naming a bot, Generated-by bots)
- staged files with banned extensions (default: .docx .xlsx)
- missing ticket reference (only with --ticket-regex)

`--staged` takes newline-separated paths; repeat it, or prefix with @ to
read the list from a file (`--staged @list.txt`). With no --staged the
tool runs `git diff --cached --name-only` itself.

Warns (exit 0) by default; with COMMIT_GATE_MODE=block a tripped gate
exits 2. Missing or unreadable inputs and an unavailable git fail open:
stderr note, exit 0, never a failure.

Works on Python 3.9+ with no third-party packages.
"""

import argparse
import json
import os
import re
import subprocess
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

SUBJECT_MAX = 50
BODY_MAX = 72

CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\(.+\))?(!)?: .{1,}$"
)

AI_WORDS = r"ai|bot|assistant|claude|copilot|cursor"
COAUTHORED_RE = re.compile(
    r"^\s*co-authored-by\s*:.*\b(%s)\b" % AI_WORDS, re.IGNORECASE
)
GENERATED_RE = re.compile(
    r"^\s*[\w-]*generated[\w-]*\s*:.*\b(ai|bot)\b", re.IGNORECASE
)
TRAILER_SHAPE_RE = re.compile(r"^\s*[\w][\w.-]*\s*:")
NARROW_AI_RE = re.compile(r"\b(ai|bot)\b", re.IGNORECASE)

# md/json stay allowed: plenty of repos commit them on purpose.
DEFAULT_BAN = {".docx", ".xlsx"}


def parse_ext_list(raw):
    """Split a comma/space-separated extension list into normalized {ext}."""
    exts = set()
    for chunk in raw.replace(",", " ").split():
        chunk = chunk.strip().lower()
        if not chunk:
            continue
        if not chunk.startswith("."):
            chunk = "." + chunk
        exts.add(chunk)
    return exts


def effective_ban(args):
    """Default bans plus --ban/COMMIT_GATE_BAN, minus --allow/COMMIT_GATE_ALLOW."""
    ban = set(DEFAULT_BAN)
    for raw in list(args.ban or []):
        ban |= parse_ext_list(raw)
    ban |= parse_ext_list(os.environ.get("COMMIT_GATE_BAN", ""))
    for raw in list(args.allow or []):
        ban -= parse_ext_list(raw)
    ban -= parse_ext_list(os.environ.get("COMMIT_GATE_ALLOW", ""))
    return ban


def read_input(path):
    """Return (text, error) for an input path. error is "" on success."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace"), ""
    except OSError as exc:
        return None, "%s: %s" % (path, exc)


def staged_from_values(values):
    """Resolve --staged values: literal newline-separated paths, @file lists.

    Returns (paths, error). error is "" on success.
    """
    paths = []
    for value in values:
        if value.startswith("@"):
            text, error = read_input(value[1:])
            if text is None:
                return None, "cannot read staged list %s" % error
            blob = text
        else:
            blob = value
        for line in blob.split("\n"):
            line = line.strip()
            if line:
                paths.append(line)
    return paths, ""


def staged_from_git():
    """Return (paths, error) from git diff --cached --name-only."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=30,
            errors="replace",
        )
    except FileNotFoundError:
        return None, "git is not available on PATH"
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "git failed: %s" % exc
    if proc.returncode != 0:
        return None, "git diff --cached failed: %s" % proc.stderr.strip()
    return [line for line in proc.stdout.split("\n") if line.strip()], ""


def split_message(text):
    """Drop git comment lines; return (subject, body_lines, subject_no, ai_hits).

    subject_no is the 1-based line number of the subject in the stripped
    text; ai_hits holds (line_no, line) for AI trailer lines.
    """
    kept = []
    for line in text.split("\n"):
        if line.startswith("#"):
            continue
        kept.append((len(kept) + 1, line))
    while kept and not kept[0][1].strip():
        kept.pop(0)
    while kept and not kept[-1][1].strip():
        kept.pop()
    if not kept:
        return "", [], 0, []
    subject_no, subject = kept[0]
    body = kept[1:]
    ai_hits = [
        (no, line) for no, line in kept
        if COAUTHORED_RE.search(line)
        or GENERATED_RE.search(line)
        or (TRAILER_SHAPE_RE.match(line) and NARROW_AI_RE.search(line))
    ]
    return subject.strip(), body, subject_no, ai_hits


def evaluate(message_text, staged, ban, ticket_regex):
    """Return the violation list for one message plus staged list."""
    violations = []
    subject, body, _, ai_hits = split_message(message_text)
    if not subject:
        violations.append("empty commit message (no subject line)")
    else:
        if len(subject) > SUBJECT_MAX:
            violations.append(
                "subject exceeds %d chars (%d): %r"
                % (SUBJECT_MAX, len(subject), subject)
            )
        if not CONVENTIONAL_RE.match(subject):
            violations.append(
                "subject is not Conventional Commits shape "
                "(type[(scope)][!]: description): %r" % subject
            )
    for no, line in body:
        if len(line) > BODY_MAX:
            violations.append(
                "body line %d exceeds %d chars (%d)"
                % (no, BODY_MAX, len(line))
            )
    for no, line in ai_hits:
        violations.append("AI trailer on line %d: %s" % (no, line.strip()))
    for path in staged:
        suffix = os.path.splitext(path)[1].lower()
        if suffix in ban:
            violations.append(
                "staged file has banned extension %s: %s" % (suffix, path)
            )
    if ticket_regex is not None and not ticket_regex.search(message_text):
        violations.append(
            "message lacks ticket reference matching %r"
            % ticket_regex.pattern
        )
    return violations


def verdict_line(violations, message_path, mode):
    """One human line plus one line per violation. Empty when clean."""
    if not violations:
        return ""
    lines = [
        "Commit gate: %d issue(s) in %s [mode=%s]"
        % (len(violations), message_path, mode)
    ]
    lines.extend("- %s" % v for v in violations)
    return "\n".join(lines)


def fail_open(args, reason, mode, message_path, staged):
    """Missing or unreadable inputs: stderr note, exit 0, never a failure."""
    print("commit-gate: %s" % reason, file=sys.stderr)
    if args.json:
        print(json.dumps({
            "ok": True,
            "violations": [],
            "mode": "block" if mode == "block" else "warn",
            "message": message_path,
            "staged": staged,
            "systemMessage": "",
            "note": reason,
        }, indent=2, ensure_ascii=False))
    return 0


def cmd_check(args):
    mode = os.environ.get("COMMIT_GATE_MODE", "")
    mode_name = "block" if mode == "block" else "warn"
    message_path = args.message_file or ""
    if not message_path:
        return fail_open(args, "no --message-file given", mode, "", [])
    message_text, error = read_input(message_path)
    if message_text is None:
        return fail_open(
            args, "cannot read message file %s" % error,
            mode, message_path, [])
    if args.staged:
        staged, error = staged_from_values(args.staged)
        if staged is None:
            return fail_open(args, error, mode, message_path, [])
    else:
        staged, error = staged_from_git()
        if staged is None:
            return fail_open(args, error, mode, message_path, [])
    ticket_regex = None
    if args.ticket_regex:
        try:
            ticket_regex = re.compile(args.ticket_regex)
        except re.error as exc:
            print("commit-gate: bad --ticket-regex: %s" % exc,
                  file=sys.stderr)
            return 2
    violations = evaluate(message_text, staged, effective_ban(args),
                          ticket_regex)
    line = verdict_line(violations, message_path, mode_name)
    if args.json:
        print(json.dumps({
            "ok": not violations,
            "violations": violations,
            "mode": mode_name,
            "message": message_path,
            "staged": staged,
            "systemMessage": line,
        }, indent=2, ensure_ascii=False))
    elif line:
        print(line)
    if violations and mode == "block":
        return 2
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="commitcheck.py",
        description="Gate commits on message shape and staged extensions.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check one commit message")
    check.add_argument("--message-file", default="",
                       help="path to the commit message file")
    check.add_argument("--staged", action="append", default=[],
                       help="newline-separated staged paths, or @file; "
                            "repeatable; default runs git diff --cached")
    check.add_argument("--ban", action="append", default=[],
                       help="extra banned extensions (comma/space separated)")
    check.add_argument("--allow", action="append", default=[],
                       help="extensions to unban (overrides --ban and env)")
    check.add_argument("--ticket-regex", default="",
                       help="message must match this regex (off by default)")
    check.add_argument("--json", action="store_true",
                       help="emit the machine-readable report")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
