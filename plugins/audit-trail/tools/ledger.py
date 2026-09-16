#!/usr/bin/env python3
"""audit-trail: zero-dependency edit ledger and review digest (stdlib only).

Two subcommands:

    <hook-event-JSON> | tools/ledger.py append
    tools/ledger.py digest [LEDGER] [--json]

`append` reads one hook event from stdin and appends one JSONL record to
the ledger. It always exits 0: bad input earns a stderr note, never a
failed hook. `digest` renders the ledger as a per-file change list with
line counts and turn refs for review.

Record schema v1: schema, ts, session, turn, tool, file, lines_added,
lines_removed, claim_refs.

Ledger path: $AUDIT_TRAIL_LEDGER, else .audit-trail/ledger.jsonl under
the current directory. Created on demand by `append`.

Works on Python 3.9+ with no third-party packages.
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
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

SCHEMA_VERSION = "v1"
LEDGER_ENV_VAR = "AUDIT_TRAIL_LEDGER"
DEFAULT_LEDGER_REL = Path(".audit-trail") / "ledger.jsonl"


def default_ledger_path() -> Path:
    """Ledger location: env override, else .audit-trail/ledger.jsonl under cwd."""
    override = os.environ.get(LEDGER_ENV_VAR, "").strip()
    if override:
        return Path(override)
    return Path.cwd() / DEFAULT_LEDGER_REL


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_int(value):
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, float):
        return max(int(value), 0)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def event_field(event, *names, default=""):
    """First usable value across naming variants: non-empty strings, plus
    non-negative numbers when the default is numeric (the turn field)."""
    for name in names:
        value = event.get(name)
        if isinstance(value, str) and value.strip():
            return value
        if (default == 0 and isinstance(value, (int, float))
                and not isinstance(value, bool) and value >= 0):
            return int(value)
    return default


def parse_hook_event(raw):
    """Build a v1 record from a hook event body. Returns (record, error).

    Accepts the Claude PostToolUse envelope (tool_name, tool_input,
    session_id) plus flat variants carrying tool/file/session/turn and an
    edited-lines payload. Returns an error string instead of a record when
    the input carries nothing worth logging.
    """
    if not raw.strip():
        return None, "empty stdin, nothing to log"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, "invalid JSON on stdin: %s" % exc
    if not isinstance(data, dict):
        return None, "hook event must be a JSON object"

    tool_input = _as_dict(data.get("tool_input"))
    tool_call_args = _as_dict(_as_dict(data.get("toolCall")).get("args"))
    args = _as_dict(data.get("args"))
    tool_response = _as_dict(data.get("tool_response"))
    merged = dict(tool_call_args)
    merged.update(args)
    merged.update(tool_input)

    file_path = (
        merged.get("file_path") or merged.get("TargetFile")
        or tool_response.get("filePath") or data.get("file") or ""
    )
    if not isinstance(file_path, str) or not file_path.strip():
        return None, "hook event names no file, nothing to log"

    tool = event_field(data, "tool_name", "tool")
    if not tool:
        candidate = merged.get("tool") or data.get("toolCall", {})
        tool = candidate if isinstance(candidate, str) else ""
    session = event_field(data, "session_id", "session")
    turn = event_field(data, "turn", "turn_number", "turnNumber", default=0)
    if not isinstance(turn, int):
        turn = 0

    edited = _as_dict(data.get("edited_lines") or data.get("editedLines"))
    added = _as_int(edited.get("added", edited.get("lines_added",
                 data.get("lines_added", merged.get("lines_added", 0)))))
    removed = _as_int(edited.get("removed", edited.get("lines_removed",
                   data.get("lines_removed", merged.get("lines_removed", 0)))))

    claims = data.get("claim_refs", data.get("claims", []))
    if isinstance(claims, str):
        claims = [claims]
    if not isinstance(claims, list):
        claims = []
    claims = [c for c in claims if isinstance(c, str) and c.strip()]

    record = OrderedDict((
        ("schema", SCHEMA_VERSION),
        ("ts", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("session", session if isinstance(session, str) else ""),
        ("turn", turn),
        ("tool", tool if isinstance(tool, str) else ""),
        ("file", file_path.strip()),
        ("lines_added", added),
        ("lines_removed", removed),
        ("claim_refs", claims),
    ))
    return record, ""


def read_ledger(path):
    """Load valid v1 records, skipping corrupt lines with a stderr note."""
    records = []
    skipped = 0
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records, skipped
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if not isinstance(record, dict) or not record.get("file"):
            skipped += 1
            continue
        records.append(record)
    if skipped:
        print("audit-trail: skipped %d corrupt ledger line(s) in %s"
              % (skipped, path), file=sys.stderr)
    return records, skipped


def summarize(records):
    """Per-file rollup plus totals, in first-seen file order."""
    files = OrderedDict()
    for record in records:
        name = record.get("file", "")
        entry = files.setdefault(name, {
            "file": name, "edits": 0, "lines_added": 0,
            "lines_removed": 0, "turns": [],
        })
        entry["edits"] += 1
        entry["lines_added"] += _as_int(record.get("lines_added", 0))
        entry["lines_removed"] += _as_int(record.get("lines_removed", 0))
        turn = record.get("turn", 0)
        if isinstance(turn, int) and turn > 0 and turn not in entry["turns"]:
            entry["turns"].append(turn)
    for entry in files.values():
        entry["turns"].sort()
    return {
        "edits": len(records),
        "files": list(files.values()),
        "lines_added": sum(e["lines_added"] for e in files.values()),
        "lines_removed": sum(e["lines_removed"] for e in files.values()),
    }


def format_turns(turns):
    if not turns:
        return "turn ?"
    if len(turns) == 1:
        return "turn %d" % turns[0]
    return "turns %s" % ", ".join(str(t) for t in turns)


def print_digest(summary):
    edits = summary["edits"]
    print("Audit digest: %d edit%s across %d file%s (+%d/-%d)" % (
        edits, "" if edits == 1 else "s",
        len(summary["files"]), "" if len(summary["files"]) == 1 else "s",
        summary["lines_added"], summary["lines_removed"]))
    for entry in summary["files"]:
        print("%s (+%d/-%d, %d edit%s, %s)" % (
            entry["file"], entry["lines_added"], entry["lines_removed"],
            entry["edits"], "" if entry["edits"] == 1 else "s",
            format_turns(entry["turns"])))


def cmd_append(_args) -> int:
    record, error = parse_hook_event(sys.stdin.read())
    if record is None:
        print("audit-trail: %s" % error, file=sys.stderr)
        return 0
    path = default_ledger_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print("audit-trail: cannot write %s: %s" % (path, exc), file=sys.stderr)
        return 0
    return 0


def cmd_digest(args) -> int:
    path = Path(args.ledger) if args.ledger else default_ledger_path()
    summary = summarize(read_ledger(path)[0])
    if not summary["edits"] and not Path(path).is_file():
        note = "audit-trail: no ledger yet at %s" % path
        if args.json:
            print(json.dumps({"note": note, "edits": 0, "files": [],
                              "lines_added": 0, "lines_removed": 0},
                             indent=2, ensure_ascii=False))
        else:
            print(note)
        return 0
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_digest(summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ledger.py",
        description="Append hook events to an edit ledger, or digest the "
                    "ledger for review.")
    sub = ap.add_subparsers(dest="command", required=True)

    apnd = sub.add_parser("append", help="log one hook event from stdin")
    apnd.set_defaults(func=cmd_append)

    dgst = sub.add_parser("digest", help="render the ledger for review")
    dgst.add_argument("ledger", nargs="?",
                     help="ledger file; defaults to $AUDIT_TRAIL_LEDGER or "
                          ".audit-trail/ledger.jsonl")
    dgst.add_argument("--json", action="store_true",
                    help="machine-readable output")
    dgst.set_defaults(func=cmd_digest)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
