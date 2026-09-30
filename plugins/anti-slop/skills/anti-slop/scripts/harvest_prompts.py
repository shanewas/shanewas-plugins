#!/usr/bin/env python3
"""
Harvest your own prompts out of Claude Code transcripts, as voice-profile corpus.

Only user-authored text survives. Tool results, hook output, slash commands,
system reminders, and pasted code are stripped, since none of it is your writing
and all of it would skew the profile.

    python harvest_prompts.py                    # write ~/.claude/voice-corpus/
    python harvest_prompts.py --out DIR --min 8  # tune destination and floor
    python harvest_prompts.py --selftest
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"

# Machine-authored text that rides inside user-role messages.
NOISE = re.compile(
    r"<system-reminder>.*?</system-reminder>"
    r"|<command-name>.*?</command-(?:name|message|args)>"
    r"|<local-command-stdout>.*?</local-command-stdout>"
    r"|<user-prompt-submit-hook>.*?</user-prompt-submit-hook>"
    r"|```.*?```"
    r"|<[a-z-]+>\s*</[a-z-]+>",
    re.DOTALL | re.IGNORECASE,
)

# A message that is mostly a path, a stack trace, or a paste isn't voice.
PASTE_MARKERS = re.compile(r"^\s*(?:[A-Z]:\\|/[a-z]+/|\s{4}at |Traceback|\{|\[|<\?xml|\S+\.(?:cs|js|json|log|txt|py)\s*$)")


def clean(text: str) -> str:
    text = NOISE.sub(" ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    lines = [ln for ln in text.splitlines() if not PASTE_MARKERS.match(ln)]
    return re.sub(r"[ \t]+", " ", "\n".join(lines)).strip()


def extract(jsonl: Path, min_words: int):
    for raw in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "user" or rec.get("isMeta"):
            continue
        content = (rec.get("message") or {}).get("content")
        if isinstance(content, list):
            # A list containing tool_result blocks is a tool turn, not a typed prompt.
            if any(b.get("type") == "tool_result" for b in content if isinstance(b, dict)):
                continue
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        if not isinstance(content, str):
            continue
        text = clean(content)
        if text.startswith("/") or len(text.split()) < min_words:
            continue
        yield text


def selftest() -> int:
    assert clean("hi <system-reminder>noise</system-reminder> there") == "hi there"
    assert clean("keep ```code block``` this") == "keep this"
    assert "C:\\x" not in clean("real words\nC:\\x\\y.cs")
    print("harvest selftest ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path.home() / ".claude" / "voice-corpus")
    ap.add_argument("--min", type=int, default=6, help="minimum words to keep a prompt")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not PROJECTS.exists():
        print(f"No transcripts at {PROJECTS}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    total_words = kept = 0
    for proj in sorted(PROJECTS.iterdir()):
        if not proj.is_dir():
            continue
        chunks = [t for f in sorted(proj.glob("*.jsonl")) for t in extract(f, args.min)]
        if not chunks:
            continue
        body = "\n\n".join(chunks)
        (args.out / f"{proj.name}.txt").write_text(body, encoding="utf-8")
        kept += len(chunks)
        total_words += len(body.split())

    print(f"{kept} prompts, {total_words} words -> {args.out}")
    print(f"Next: python detect_slop.py --learn {args.out}/*.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
