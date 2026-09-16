#!/usr/bin/env python3
"""minimal-diff: zero-dependency diff-size gate (stdlib only).

Reads one unified diff and warns when the change looks too big to
review in one pass:

    tools/diffgate.py check [DIFF] [--max-files N] [--max-lines N]
                            [--max-concerns N] [--hook]

With no DIFF, `check` reads the diff from stdin, so it slots behind
`git diff` in hooks and scripts. It reports files touched, lines
added/removed, and a concern heuristic (the larger of distinct
top-level dirs and distinct file extensions) as a rough proxy for
how many ideas the change spans.

Warns and exits 0 when files > 5, added+removed > 400, or concerns > 3.
Thresholds yield to flags first, then DIFF_GATE_MAX_FILES /
DIFF_GATE_MAX_LINES / DIFF_GATE_MAX_CONCERNS, then the built-ins. With
DIFF_GATE_MODE=block a tripped gate exits 2 instead. Input that holds
no unified-diff content passes open: exit 0 with a stderr note, never
a failure.

Works on Python 3.9+ with no third-party packages.
"""

import argparse
import json
import os
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

DEFAULT_MAX_FILES = 5
DEFAULT_MAX_LINES = 400
DEFAULT_MAX_CONCERNS = 3

BLOCK_EXIT = 2


def _strip_prefix(path):
    """Drop the a/ or b/ prefix git puts on diff paths."""
    if len(path) > 2 and path[1] == "/" and path[0] in ("a", "b"):
        return path[2:]
    return path


def _diff_git_path(line):
    """Path from a `diff --git a/old b/new` header. New side wins."""
    parts = line.split(" ")
    if len(parts) < 4:
        return ""
    path = parts[3].strip().strip('"')
    return _strip_prefix(path)


def _plus_path(line):
    """Path from a `+++ b/path` header. Empty for /dev/null."""
    path = line[4:].strip().split("\t")[0].strip().strip('"')
    if path == "/dev/null":
        return ""
    return _strip_prefix(path)


def parse_diff(text):
    """Map each touched path to (added, removed) line counts.

    Returns None when the text holds no unified-diff markers at all,
    so callers can fail open instead of scoring prose as a diff.
    """
    files = {}
    current = None
    saw_marker = False
    for line in text.splitlines():
        if line.startswith("diff --git "):
            saw_marker = True
            path = _diff_git_path(line)
            current = path or None
            if path:
                files.setdefault(path, [0, 0])
        elif line.startswith("+++ "):
            saw_marker = True
            path = _plus_path(line)
            if path:
                current = path
                files.setdefault(path, [0, 0])
        elif line.startswith("--- ") or line.startswith("@@ "):
            saw_marker = True
        elif current is not None and line.startswith("+") \
                and not line.startswith("+++"):
            files[current][0] += 1
        elif current is not None and line.startswith("-") \
                and not line.startswith("---"):
            files[current][1] += 1
    if not saw_marker:
        return None
    return {path: (counts[0], counts[1]) for path, counts in files.items()}


def concerns_of(paths):
    """Rough concern proxy: max(distinct top-level dirs,
    distinct file extensions)."""
    dirs = set()
    exts = set()
    for path in paths:
        parts = path.split("/")
        dirs.add(parts[0] if len(parts) > 1 else "(root)")
        base = parts[-1]
        exts.add(base.rsplit(".", 1)[1].lower() if "." in base else "(none)")
    return max(len(dirs), len(exts))


def resolve_threshold(flag, env_name, default):
    """Flag wins, then env, then built-in. Bad env values fall back."""
    if flag is not None:
        return flag
    raw = os.environ.get(env_name)
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            print("diff-gate: ignoring invalid %s=%r" % (env_name, raw),
                  file=sys.stderr)
    return default


def warn_line(n_files, added, removed, concerns, limits):
    """Warning body: counts against limits plus what tripped."""
    max_files, max_lines, max_concerns = limits
    tripped = []
    if n_files > max_files:
        tripped.append("files %d > %d" % (n_files, max_files))
    if added + removed > max_lines:
        tripped.append("lines %d > %d" % (added + removed, max_lines))
    if concerns > max_concerns:
        tripped.append("concerns %d > %d" % (concerns, max_concerns))
    return ("Diff gate: files=%d (max %d), lines=+%d/-%d (max %d), "
            "concerns=%d (max %d). Tripped: %s. "
            "Split the change into smaller reviews."
            % (n_files, max_files, added, removed, max_lines,
               concerns, max_concerns, ", ".join(tripped)))


def read_input(path):
    """Diff text from a file, or stdin when no path is given."""
    if path is None:
        return sys.stdin.read()
    if not Path(path).is_file():
        return None
    return Path(path).read_text(encoding="utf-8", errors="replace")


def hook_report(text, blocking):
    """Strict hook-runtime JSON: only keys hook-output schemas accept
    (systemMessage plus decision/reason when blocking). Always exits 0:
    blocking travels in the decision field, never the exit code, because
    hook runtimes drop the message on nonzero exit."""
    payload = {"systemMessage": text}
    if blocking:
        payload = {"decision": "block",
                   "reason": text.split("\n")[0][:200],
                   "systemMessage": text}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_check(args):
    text = read_input(args.diff)
    if text is None:
        return 0
    if not text.strip():
        return 0
    files = parse_diff(text)
    if files is None:
        print("diff-gate: no unified-diff content found, passing open",
              file=sys.stderr)
        return 0
    added = sum(counts[0] for counts in files.values())
    removed = sum(counts[1] for counts in files.values())
    concerns = concerns_of(files)
    limits = (
        resolve_threshold(args.max_files, "DIFF_GATE_MAX_FILES",
                          DEFAULT_MAX_FILES),
        resolve_threshold(args.max_lines, "DIFF_GATE_MAX_LINES",
                          DEFAULT_MAX_LINES),
        resolve_threshold(args.max_concerns, "DIFF_GATE_MAX_CONCERNS",
                          DEFAULT_MAX_CONCERNS),
    )
    if len(files) <= limits[0] and added + removed <= limits[1] \
            and concerns <= limits[2]:
        return 0
    if args.hook:
        return hook_report(
            warn_line(len(files), added, removed, concerns, limits),
            os.environ.get("DIFF_GATE_MODE") == "block")
    print(warn_line(len(files), added, removed, concerns, limits))
    if os.environ.get("DIFF_GATE_MODE") == "block":
        return BLOCK_EXIT
    return 0


def build_parser():
    ap = argparse.ArgumentParser(
        prog="diffgate.py",
        description="Warn (or block) when a unified diff is too big "
                    "for one review.")
    sub = ap.add_subparsers(dest="command", required=True)
    ch = sub.add_parser("check", help="gate one unified diff")
    ch.add_argument("diff", nargs="?",
                    help="diff file to check; omit to read from stdin")
    ch.add_argument("--max-files", type=int, default=None,
                    help="trip above this many files (default %d, "
                         "DIFF_GATE_MAX_FILES also works)" % DEFAULT_MAX_FILES)
    ch.add_argument("--max-lines", type=int, default=None,
                    help="trip above this many added+removed lines "
                         "(default %d, DIFF_GATE_MAX_LINES also works)"
                         % DEFAULT_MAX_LINES)
    ch.add_argument("--max-concerns", type=int, default=None,
                    help="trip above this concern proxy (default %d, "
                         "DIFF_GATE_MAX_CONCERNS also works)"
                         % DEFAULT_MAX_CONCERNS)
    ch.add_argument("--hook", action="store_true",
                    help="strict hook-runtime JSON (accepted keys only), "
                         "always exit 0; blocking uses decision:block")
    ch.set_defaults(func=cmd_check)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
