#!/usr/bin/env python3
"""slop-gate: zero-dependency AI-slop scorer and edit gate (stdlib only).

Unifies the anti-slop detector phrase lists and voice metrics into one
small CLI with three subcommands:

    tools/slop.py score FILE [--json] [--verbose]
    tools/slop.py check [FILE] [--threshold N] [--json]
    tools/slop.py learn SAMPLE... [--profile PATH]

Score bands: <20 clean, 20-40 marginal, 40-60 heavy, >60 severe.
Scoring is flat additive per hit up to 500 words, so a small
edit carrying strong slop signals still trips the gate; above 500 words
the phrase-hit subtotal scales as if the text were 500 words long.
Rhythm deviations are per-word normalized throughout. `check` prints a
warning and exits 0 by default; with SLOP_GATE_MODE=block it exits 2 when
the score reaches the threshold. With no FILE, `check` reads a hook event
(JSON on stdin) and scores the edited file named there.

Works on Python 3.9+ with no third-party packages.
"""

import argparse
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

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

# Rhythm metrics only make sense on prose. Running them over .cs/.js produces
# noise, so structural analysis is gated on these suffixes.
PROSE_EXTS = {".md", ".txt", ".rst", ""}

# Flat points per hit. Small integers keep gate scores exact and pinnable.
WEIGHTS = {
    "high_risk": 10,
    "thesaurus": 8,
    "japanese_slop": 10,
    "meta_commentary": 8,
    "medium_risk": 5,
    "buzzwords": 5,
    "hedging": 4,
    "structure": 10,
}

RHYTHM_PER_DEVIATION = 6
RHYTHM_CAP = 30
DEFAULT_THRESHOLD = 20

# Phrase hits are raw counts, so long documents accumulate noise past the
# bands. Above this many words the phrase subtotal scales as if the text
# were this long; shorter texts score exactly as before.
LENGTH_NORM_WORDS = 500

# High-risk phrases that nearly always indicate AI slop.
HIGH_RISK_PHRASES = [
    r"delve into",
    r"dive deep into",
    r"unpack",
    r"navigate the complexit(?:y|ies)",
    r"in the ever-evolving landscape",
    r"in today's fast-paced world",
    r"in today's digital age",
    r"at the end of the day",
    r"it'?s important to note that",
    r"it'?s worth noting that",
    r"tapestry of",
    r"a testament to",
    r"in the realm of",
    r"when it comes to",
    r"not just\b.*?\bbut (?:also\b)?",
    r"buckle up",
    r"take it to the next level",
    r"unlock the power of",
    r"supercharge your",
    r"move the needle",
    r"without further ado",
    r"i hope this (?:email|message)?\s*finds you well",
    r"please don'?t hesitate to reach out",
    r"feel free to reach out",
    r"happy to dig deeper",
    r"let me know if you(?:'d like me to| have any questions)",
    r"^\s*Repro:\s*$",
    r",\s*ensuring\b",
    r",\s*so you can'?t lock yourself out\b",
]

# Medium-risk phrases - context dependent.
MEDIUM_RISK_PHRASES = [
    r"however,? it is important to",
    r"furthermore",
    r"moreover",
    r"in essence",
    r"essentially",
    r"fundamentally",
    r"ultimately",
    r"that being said",
]

# Buzzwords and corporate jargon.
BUZZWORDS = [
    r"synergistic",
    r"holistic approach",
    r"paradigm shift",
    r"game-changer",
    r"revolutionary",
    r"cutting-edge",
    r"next-generation",
    r"world-class",
    r"best-in-class",
    r"leverage",
    r"utilize",
    r"empower",
    r"unlock potential",
    r"drive innovation",
    r"\bdelv(?:e|es|ing)\b",
    r"\bvibrant\b",
    r"\bpivotal\b",
    r"\bintricate\b",
    r"\bmeticulous(?:ly)?\b",
    r"\bbolster(?:ed|ing)?\b",
    r"\bgarner(?:ed|ing)?\b",
    r"\bunderscore(?:s|d)?\b",
    r"\bmultifaceted\b",
    r"\bgroundbreaking\b",
    r"\btransformative\b",
    r"\brevolutioni[sz]e\b",
    r"\bseamless(?:ly)?\b",
    r"\brobust\b",
    r"\bseamless integration\b",
    r"\balign with\b",
    r"\bstreamline(?:s|d|ing)?\b",
    r"\bfoster(?:s|ed|ing)?\b",
    r"\bholistic\b",
    r"\bspearhead(?:s|ed|ing)?\b",
    r"\bkey takeaway[s]?\b",
    r"\bin terms of\b",
    r"\bat the heart of\b",
    r"\bfoundational\b",
    r"\binterplay\b",
    r"\bparamount\b",
]

# Japanese AI slop patterns (form-letter padding, vague verbs, tail phrases).
JP_SLOP_PHRASES = [
    r"ご確認のほどよろしくお願いいたします",
    r"ご査収のほどよろしくお願いいたします",
    r"恐れ入りますが",
    r"幸甚に存じます",
    r"何卒よろしくお願い申し上げます",
    r"と言えるでしょう",
    r"が期待されます",
    r"重要なポイントです",
    r"と考えられます",
    r"言わずもがな",
    r"実施してまいります",
    r"注力してまいります",
    r"検討を重ねて",
    r"推進する",
    r"寄与する",
    r"仕様書参照",
    r"SDF_\w+",
]

# Meta-commentary patterns.
META_COMMENTARY = [
    r"in this (?:article|post|document|section)",
    r"as we (?:explore|examine|discuss|delve)",
    r"let'?s take a (?:closer )?look",
    r"now that we'?ve covered",
    r"before we proceed",
    r"it'?s crucial to understand",
]

# Excessive hedging.
HEDGE_WORDS = [
    r"may or may not",
    r"could potentially",
    r"might possibly",
    r"it appears that",
    r"it seems that",
    r"one could argue",
    r"some might say",
    r"to a certain extent",
    r"generally speaking",
]

# Humanizer tells: moves that evade detectors by damaging the text.
THESAURUS_TELLS = [
    r"\bthe (?:feline|canine)\b",
    r"\bpermeated the (?:room|air)\b",
    r"\bsaid (?:individual|entity)\b",
    r"\bcommence\b",
    r"\bendeavou?r to\b",
    r"\bmyriad of\b",
    r"\bplethora\b",
    r"\bin order to\b",
]

SENTENCE_SPLIT = re.compile(r"[.!?]+[\s\"')\]]+|\n{2,}|[。！？]+[\"'」』）】\s]*")
CJK_CHAR = re.compile("[\u3040-\u309f\u30a0-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
CONTRACTION = re.compile(r"\b\w+['’](?:t|s|re|ve|ll|d|m)\b", re.IGNORECASE)
PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b", re.IGNORECASE
)
TRIAD = re.compile(r"\b\w+,\s+\w+,?\s+and\s+\w+\b")
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
DIGIT_OR_SYMBOL = re.compile(r"[0-9%$&#@*/+=<>]")

AUXILIARIES = {
    "is", "are", "was", "were", "be", "been", "being", "am",
    "has", "have", "had", "do", "does", "did",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
}

# Length-normalized vocabulary window. Type-token ratio falls as text grows, so
# comparing a 200-word note to a 2000-word doc without windowing is meaningless.
TTR_WINDOW = 200

# Detection studies put reliable separation at 300+ words. Under that, rhythm
# deviations count half rather than full.
CONFIDENCE_FLOOR_WORDS = 300

# Heuristic starting points, not measurements. Replace with your own numbers
# via `learn` — a profile beats a guessed constant.
DEFAULT_PROFILE = {
    "burstiness": 0.55,
    "em_dash_per_500w": 1.0,
    "contractions_per_100w": 1.5,
    "passive_per_100w": 2.0,
    "triads_per_1000w": 4.0,
    "max_parataxis_run": 2,
    "type_token_ratio": 0.62,
    "hapax_ratio": 0.52,
    "repeated_trigram_ratio": 0.03,
    "aux_per_100w": 9.0,
    "digit_symbol_per_100w": 3.0,
}

PROFILE_PATH = Path.home() / ".slop-gate" / "voice-profile.json"


def band_for_score(score: int) -> str:
    """Map a 0-100 score to its band label. Boundaries are exact."""
    if score < 20:
        return "clean"
    if score < 40:
        return "marginal"
    if score < 60:
        return "heavy"
    return "severe"


def summarize(score: int) -> str:
    """One-line human summary for a score."""
    band = band_for_score(score)
    return {
        "clean": "Clean - prose reads human, no action needed",
        "marginal": "Marginal - minor AI patterns worth a quick pass",
        "heavy": "Heavy - strong AI signals, revise before shipping",
        "severe": "Severe - generic machine slop, rewrite from scratch",
    }[band]


def strip_markup(text: str) -> str:
    """Reduce a document to its prose. Tables, frontmatter, code are not sentences."""
    text = re.sub(r"\A---\n.*?\n---\n", " ", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^\s*\|.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", text, flags=re.MULTILINE)
    return text


def sentences(text: str) -> List[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(strip_markup(text)) if s.strip()]


def _parataxis_len(s: str) -> int:
    """Short-sentence length. Japanese has no word spaces, count CJK chars there."""
    cjk = len(CJK_CHAR.findall(s))
    if not cjk:
        return len(s.split())
    latin = sum(1 for t in s.split() if not CJK_CHAR.search(t))
    return cjk + latin


def measure(text: str, ignore: set = frozenset()) -> Dict[str, float]:
    """Structural fingerprint of a piece of prose. Same shape for text and profile."""
    words = text.split()
    wc = max(len(words), 1)
    sents = sentences(text)
    lengths = [len(s.split()) for s in sents] or [0]
    mean_len = statistics.fmean(lengths)

    run = best_run = 0
    for s in sents:
        n = _parataxis_len(s)
        if n <= 8 and not re.search(r"[,;:、；：]|\b(?:because|although|while|which|so that)\b", s):
            run += 1
            best_run = max(best_run, run)
        else:
            run = 0

    toks = [t for t in WORD.findall(text.lower()) if t not in ignore]
    return {
        "words": len(words),
        "sentences": len(sents),
        "mean_sentence_len": round(mean_len, 2),
        "burstiness": round(statistics.pstdev(lengths) / mean_len, 3) if mean_len else 0.0,
        "em_dash_per_500w": round(text.count("\u2014") / wc * 500, 2),
        "contractions_per_100w": round(len(CONTRACTION.findall(text)) / wc * 100, 2),
        "passive_per_100w": round(len(PASSIVE.findall(text)) / wc * 100, 2),
        "triads_per_1000w": round(len(TRIAD.findall(text)) / wc * 1000, 2),
        "max_parataxis_run": best_run,
        "type_token_ratio": windowed_ttr(toks),
        "hapax_ratio": hapax_ratio(toks),
        "repeated_trigram_ratio": repeated_trigram_ratio(toks),
        "aux_per_100w": round(sum(t in AUXILIARIES for t in toks) / wc * 100, 2),
        "digit_symbol_per_100w": round(
            sum(bool(DIGIT_OR_SYMBOL.search(w)) for w in words) / wc * 100, 2
        ),
    }


def edits1(word: str) -> set:
    """Every string one edit away: transposition, deletion, substitution, insertion."""
    letters = "abcdefghijklmnopqrstuvwxyz'"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    return {
        *(a + b[1:] for a, b in splits if b),
        *(a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1),
        *(a + c + b[1:] for a, b in splits if b for c in letters),
        *(a + c + b for a, b in splits for c in letters),
    }


def find_typos(toks: List[str]) -> set:
    """Rare tokens within one edit of a frequent one. The corpus is its own
    dictionary: words the author uses repeatedly are correct by definition."""
    counts = defaultdict(int)
    for t in toks:
        counts[t] += 1

    freq_set = {w for w, c in counts.items() if c >= 5 and len(w) > 3}
    typos = set()
    for w, c in counts.items():
        if c > 1 or len(w) <= 3:
            continue
        hits = edits1(w) & freq_set
        # A one-edit difference at the tail is inflection, not error.
        if any(len(os.path.commonprefix([w, m])) < len(w) - 1 for m in hits):
            typos.add(w)
    return typos


def windowed_ttr(toks: List[str]) -> float:
    """Vocabulary richness, averaged over fixed windows so length doesn't skew it."""
    if not toks:
        return 0.0
    windows = [toks[i:i + TTR_WINDOW] for i in range(0, len(toks), TTR_WINDOW)]
    if len(windows) > 1 and len(windows[-1]) < TTR_WINDOW // 2:
        windows.pop()
    return round(statistics.fmean(len(set(w)) / len(w) for w in windows), 3)


def hapax_ratio(toks: List[str]) -> float:
    """Share of vocabulary used exactly once. Falls when words get recycled."""
    if not toks:
        return 0.0
    counts = defaultdict(int)
    for t in toks:
        counts[t] += 1
    return round(sum(1 for c in counts.values() if c == 1) / len(counts), 3)


def repeated_trigram_ratio(toks: List[str]) -> float:
    """Share of word trigrams appearing more than once."""
    if len(toks) < 4:
        return 0.0
    counts = defaultdict(int)
    for i in range(len(toks) - 2):
        counts[(toks[i], toks[i + 1], toks[i + 2])] += 1
    return round(sum(1 for c in counts.values() if c > 1) / len(counts), 3)


def load_profile(path: Path = PROFILE_PATH) -> Tuple[Dict[str, float], str]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))["profile"], str(path)
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    return dict(DEFAULT_PROFILE), "built-in defaults (run learn for your own)"


# Metrics the medium dictates rather than the author. Chat prompts are fragments
# with no punctuation, so learning these from a chat corpus teaches the wrong
# lesson. Learn them from real prose or not at all.
MEDIUM_BOUND = {
    "burstiness", "max_parataxis_run", "contractions_per_100w", "repeated_trigram_ratio",
    "passive_per_100w", "aux_per_100w", "triads_per_1000w",
}


def is_fragmentary(metrics: Dict[str, float]) -> bool:
    return metrics["mean_sentence_len"] < 12 or metrics["max_parataxis_run"] > 6


def learn_profile(sample_paths: List[str], out: Path = PROFILE_PATH) -> Dict:
    """Build a voice profile from writing you actually wrote."""
    bodies = []
    for p in sample_paths:
        try:
            body = Path(p).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print("skip %s: %s" % (p, e), file=sys.stderr)
            continue
        if len(body.split()) < 30:
            print("skip %s: under 30 words, too short" % p, file=sys.stderr)
            continue
        bodies.append(body)

    typos = find_typos(WORD.findall(strip_markup("\n".join(bodies)).lower()))
    per_sample = [measure(b, ignore=typos) for b in bodies]

    if not per_sample:
        raise SystemExit("No usable samples. Need files of 30+ words that you wrote.")

    keys = [k for k in DEFAULT_PROFILE if k != "max_parataxis_run"]
    profile = {k: round(statistics.median(m[k] for m in per_sample), 3) for k in keys}
    profile["max_parataxis_run"] = max(m["max_parataxis_run"] for m in per_sample)
    profile["mean_sentence_len"] = round(
        statistics.median(m["mean_sentence_len"] for m in per_sample), 2)

    fragmentary = sum(is_fragmentary(m) for m in per_sample) > len(per_sample) / 2
    dropped = []
    if fragmentary:
        dropped = sorted(MEDIUM_BOUND)
        for k in dropped:
            profile[k] = DEFAULT_PROFILE[k]

    payload = {
        "profile": profile,
        "samples": len(per_sample),
        "total_words": sum(m["words"] for m in per_sample),
        "sources": [str(Path(p).name) for p in sample_paths],
        "fragmentary_corpus": fragmentary,
        "defaulted_metrics": dropped,
        "typos_excluded": len(typos),
        "typo_sample": sorted(typos)[:15],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


class SlopGate:
    def __init__(self, filepath: str, profile: Dict[str, float] = None,
                 profile_src: str = ""):
        self.filepath = Path(filepath)
        self.text = self.filepath.read_text(encoding="utf-8", errors="replace")
        self.lines = self.text.split("\n")
        self.findings = defaultdict(list)  # type: Dict[str, list]
        self.profile = profile if profile is not None else dict(DEFAULT_PROFILE)
        self.profile_src = profile_src
        self.is_prose = self.filepath.suffix.lower() in PROSE_EXTS
        self.metrics = {}  # type: Dict[str, float]
        self.deviations = []  # type: List[Dict]
        self.low_confidence = False

    def _find_patterns(self, patterns: List[str], category: str):
        for i, line in enumerate(self.lines, 1):
            for pattern in patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    self.findings[category].append({
                        "line": i,
                        "text": line.strip(),
                        "match": match.group(),
                        "position": match.start(),
                    })

    def analyze(self) -> Dict:
        self.findings = defaultdict(list)
        self.metrics = {}
        self.deviations = []
        self._find_patterns(HIGH_RISK_PHRASES, "high_risk")
        self._find_patterns(MEDIUM_RISK_PHRASES, "medium_risk")
        self._find_patterns(BUZZWORDS, "buzzwords")
        self._find_patterns(META_COMMENTARY, "meta_commentary")
        self._find_patterns(HEDGE_WORDS, "hedging")
        self._find_patterns(THESAURUS_TELLS, "thesaurus")
        self._find_patterns(JP_SLOP_PHRASES, "japanese_slop")

        self._analyze_structure()
        if self.is_prose:
            self._analyze_rhythm()

        score = self._calculate_score()
        return {
            "file": str(self.filepath),
            "findings": dict(self.findings),
            "score": score,
            "band": band_for_score(score),
            "metrics": self.metrics,
            "deviations": self.deviations,
            "low_confidence": self.low_confidence,
            "summary": summarize(score),
        }

    def _analyze_rhythm(self):
        """Structural signals the phrase list can't see."""
        self.metrics = measure(self.text)
        if self.metrics["sentences"] < 4:
            return
        self.low_confidence = self.metrics["words"] < CONFIDENCE_FLOOR_WORDS

        p = self.profile
        checks = [
            ("burstiness", "below", p["burstiness"] * 0.7,
             "sentence lengths too uniform - mix short with long"),
            ("em_dash_per_500w", "above", max(p["em_dash_per_500w"], 1.0),
             "em dash overuse - swap for commas, colons, or a full stop"),
            ("contractions_per_100w", "below", p["contractions_per_100w"] * 0.5,
             "too few contractions - write don't, not do not"),
            ("passive_per_100w", "above", max(p["passive_per_100w"] * 1.6, 1.5),
             "passive pile-up - name who does the thing"),
            ("triads_per_1000w", "above", max(p["triads_per_1000w"] * 1.6, 2.0),
             "rule-of-three habit - use two items, or four"),
            ("max_parataxis_run", "above", p["max_parataxis_run"],
             "parataxis - short declaratives in a row, connect them"),
            ("type_token_ratio", "below", p["type_token_ratio"] * 0.85,
             "thin vocabulary - same words recycled"),
            ("hapax_ratio", "below", p["hapax_ratio"] * 0.85,
             "few words used once - reach past the first word"),
            ("repeated_trigram_ratio", "above",
             max(p["repeated_trigram_ratio"] * 1.5, 0.02),
             "repeated phrasing - flat n-gram spread"),
            ("aux_per_100w", "above", max(p["aux_per_100w"] * 1.4, 8.0),
             "auxiliary verb pile-up - use verbs that do something"),
            ("digit_symbol_per_100w", "above", p["digit_symbol_per_100w"] * 2.5,
             "numbers and symbols dense enough to read as formulaic"),
        ]
        has_latin = bool(WORD.search(self.text.lower()))
        for key, direction, limit, advice in checks:
            if key == "contractions_per_100w" and not has_latin:
                continue
            actual = self.metrics[key]
            tripped = (actual < limit if direction == "below" else actual > limit)
            if tripped:
                self.deviations.append({
                    "metric": key, "actual": actual,
                    "limit": round(limit, 3), "direction": direction,
                    "advice": advice,
                })

    def _analyze_structure(self):
        if self.lines:
            first_para = " ".join(self.lines[:5])
            if re.search(r"in this .+ (?:will|we)", first_para, re.IGNORECASE):
                self.findings["structure"].append({
                    "issue": "Opening meta-commentary",
                    "description": "Document opens with meta-commentary, not content",
                })

        transitions = ("however", "furthermore", "moreover", "additionally",
                       "nevertheless", "consequently", "therefore")
        starters = sum(1 for line in self.lines
                       if line.strip() and line.strip().lower().startswith(transitions))
        nonempty = [line for line in self.lines if line.strip()]
        if nonempty and starters / len(nonempty) > 0.3:
            self.findings["structure"].append({
                "issue": "Excessive transitions",
                "description": "%d%% of lines start with transition words"
                             % round(starters / len(nonempty) * 100),
            })

    def _calculate_score(self) -> int:
        """Flat additive score, capped at 100. Phrase hits are raw counts,
        so above LENGTH_NORM_WORDS words the phrase subtotal scales as if
        the text were LENGTH_NORM_WORDS long; shorter texts score exactly
        as before, and rhythm deviations are per-word normalized throughout."""
        phrase = 0
        for category, weight in WEIGHTS.items():
            phrase += len(self.findings[category]) * weight
        words = max(len(self.text.split()), 1)
        if words > LENGTH_NORM_WORDS:
            phrase = int(phrase * LENGTH_NORM_WORDS / words)

        score = phrase
        per_deviation = RHYTHM_PER_DEVIATION // 2 if self.low_confidence \
            else RHYTHM_PER_DEVIATION
        score += min(len(self.deviations) * per_deviation, RHYTHM_CAP)
        return min(score, 100)

    def warn_lines(self, threshold: int) -> List[str]:
        """Warning body shared by text and JSON check output."""
        results = self.analyze()
        head = "Slop gate: %s score=%d/100 (%s) reached threshold %d. %s" % (
            self.filepath.name, results["score"], results["band"],
            threshold, results["summary"])
        lines = [head]
        for cat, label in (("high_risk", "phrase"), ("thesaurus", "humanizer tell"),
                           ("meta_commentary", "meta"), ("buzzwords", "buzzword"),
                           ("japanese_slop", "JP slop"), ("hedging", "hedge"),
                           ("medium_risk", "filler")):
            for hit in results["findings"].get(cat) or []:
                lines.append("  L%d %s: '%s'" % (hit["line"], label, hit["match"]))
        for item in results["findings"].get("structure") or []:
            lines.append("  structural: %s" % item["issue"])
        for dev in results["deviations"]:
            arrow = "down" if dev["direction"] == "below" else "up"
            lines.append("  %s %s %s (limit %s): %s" % (
                arrow, dev["metric"], dev["actual"], dev["limit"], dev["advice"]))
        return lines

    def print_report(self, verbose: bool = False):
        results = self.analyze()
        print("Slop report: %s" % self.filepath.name)
        print("Score: %d/100 (%s)" % (results["score"], results["band"]))
        print("%s" % results["summary"])
        print("Profile: %s" % (self.profile_src or "built-in defaults"))
        for cat in ("high_risk", "buzzwords", "meta_commentary", "hedging",
                    "medium_risk", "thesaurus", "japanese_slop"):
            hits = results["findings"].get(cat) or []
            if not hits:
                continue
            print("%s (%d):" % (cat, len(hits)))
            shown = hits if verbose else hits[:5]
            for hit in shown:
                print("  L%d: '%s'" % (hit["line"], hit["match"]))
            if not verbose and len(hits) > 5:
                print("  ... and %d more" % (len(hits) - 5))
        for item in results["findings"].get("structure") or []:
            print("structural: %s - %s" % (item["issue"], item["description"]))
        if results["deviations"]:
            note = " (under 300 words, weak signal)" if results["low_confidence"] else ""
            print("Voice deviations%s:" % note)
            for dev in results["deviations"]:
                print("  %s %s: %s (limit %s) - %s" % (
                    dev["direction"], dev["metric"], dev["actual"],
                    dev["limit"], dev["advice"]))
        elif self.is_prose and results["metrics"].get("sentences", 0) >= 4:
            print("Voice: within profile")


def hook_file_from_stdin() -> str:
    """Extract the edited file path from a hook event on stdin.

    Accepts the Claude PostToolUse envelope plus common variants. Returns ""
    when stdin carries no usable path, so the gate stays silent, never loud.
    """
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    tool_input = (data.get("tool_input") or data.get("toolCall", {}).get("args")
                  or data.get("args") or {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    path = (tool_input.get("file_path") or tool_input.get("TargetFile")
            or (data.get("tool_response") or {}).get("filePath") or "")
    return path if isinstance(path, str) else ""


def resolve_profile(args) -> Tuple[Dict[str, float], str]:
    if args.no_profile:
        return dict(DEFAULT_PROFILE), "built-in defaults"
    return load_profile(args.profile)


def cmd_score(args) -> int:
    if not Path(args.file).is_file():
        print("slop-gate: file not found: %s" % args.file, file=sys.stderr)
        return 1
    profile, src = resolve_profile(args)
    gate = SlopGate(args.file, profile, src)
    if args.json:
        print(json.dumps(gate.analyze(), indent=2, ensure_ascii=False))
    else:
        gate.print_report(verbose=args.verbose)
    return 0


def cmd_check(args) -> int:
    target = args.file or hook_file_from_stdin()
    if not target or not Path(target).is_file():
        return 0
    profile, src = resolve_profile(args)
    gate = SlopGate(target, profile, src)
    results = gate.analyze()
    if results["score"] < args.threshold:
        return 0
    lines = gate.warn_lines(args.threshold)
    if args.json:
        print(json.dumps({
            "systemMessage": "\n".join(lines),
            "score": results["score"],
            "band": results["band"],
            "threshold": args.threshold,
            "file": str(target),
        }, indent=2, ensure_ascii=False))
    else:
        print("\n".join(lines))
    if os.environ.get("SLOP_GATE_MODE") == "block":
        return 2
    return 0


def cmd_learn(args) -> int:
    payload = learn_profile(args.samples, args.profile)
    print("Voice profile written: %s" % args.profile)
    print("  %d samples, %d words" % (payload["samples"], payload["total_words"]))
    for key, value in payload["profile"].items():
        tag = ("  (default, corpus too fragmentary)"
               if key in payload["defaulted_metrics"] else "")
        print("  %s: %s%s" % (key, value, tag))
    if payload["typos_excluded"]:
        print("  %d misspellings excluded, e.g. %s" % (
            payload["typos_excluded"], ", ".join(payload["typo_sample"][:8])))
    if payload["fragmentary_corpus"]:
        print("  Corpus reads as chat or notes, not prose. Rhythm metrics left "
              "at defaults; add longer prose you wrote to learn those too.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="slop.py",
        description="Score AI slop in a file, gate edits on a threshold, "
                    "or learn your voice profile.")
    sub = ap.add_subparsers(dest="command", required=True)

    sc = sub.add_parser("score", help="report score and band for a file")
    sc.add_argument("file", help="file to score")
    sc.add_argument("-v", "--verbose", action="store_true",
                    help="show every hit, not just the first five per category")
    sc.add_argument("--json", action="store_true", help="machine-readable output")
    sc.add_argument("--profile", type=Path, default=PROFILE_PATH,
                    help="voice profile path")
    sc.add_argument("--no-profile", action="store_true",
                    help="ignore any learned profile, use built-in defaults")
    sc.set_defaults(func=cmd_score)

    ch = sub.add_parser("check", help="warn (or block) when a file trips the gate")
    ch.add_argument("file", nargs="?",
                    help="file to check; omit to read a hook event from stdin")
    ch.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help="trip score (default %d)" % DEFAULT_THRESHOLD)
    ch.add_argument("--json", action="store_true",
                    help="emit a systemMessage envelope for hook runtimes")
    ch.add_argument("--profile", type=Path, default=PROFILE_PATH,
                    help="voice profile path")
    ch.add_argument("--no-profile", action="store_true",
                    help="ignore any learned profile, use built-in defaults")
    ch.set_defaults(func=cmd_check)

    ln = sub.add_parser("learn", help="build a voice profile from your writing")
    ln.add_argument("samples", nargs="+", metavar="SAMPLE",
                    help="files of prose you wrote (30+ words each)")
    ln.add_argument("--profile", type=Path, default=PROFILE_PATH,
                    help="where to write the profile")
    ln.set_defaults(func=cmd_learn)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
