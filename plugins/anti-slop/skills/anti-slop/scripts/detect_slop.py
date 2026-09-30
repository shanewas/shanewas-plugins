#!/usr/bin/env python3
"""
AI Slop Detector - Analyzes text for common AI-generated content patterns.

Three layers:
  1. Phrase lists (high/medium risk, buzzwords, meta-commentary, hedging, ...).
  2. Document structure (opening meta-commentary, transition pile-ups, formatting tells).
  3. Sentence rhythm measured against a voice profile you can learn from your own writing.
"""

from __future__ import annotations

import argparse
import json
import math
import os.path
import re
import statistics
import sys
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

__version__ = "2.0.0"

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Rhythm metrics only make sense on prose. Running them over .cs/.js produces
# noise, so structural analysis is gated on these suffixes.
PROSE_EXTS = {".md", ".markdown", ".txt", ".rst", ".adoc", ""}
SCAN_EXTS = (PROSE_EXTS - {""}) | {".html", ".tex", ".org"}

# High-risk phrases that nearly always indicate AI slop
HIGH_RISK_PHRASES = [
    r"delve into",
    r"dive deep into",
    r"(?:let'?s|to|we)\s+unpack\b|\bunpack\b\s+(?:this|what|how|the\s+(?:meaning|concept|nuance|implications?))",
    r"navigate the complexit(?:y|ies)",
    r"in the ever-evolving landscape",
    r"in today's fast-paced world",
    r"in today's digital age",
    r"at the end of the day",
    r"it(?:'s| is) important to note that",
    r"it(?:'s| is) worth noting that",
    r"tapestry of",
    r"a testament to",
    r"in the realm of",
    r"when it comes to",
    # Same sentence only, and bounded. The original `.*?` ran across whole lines.
    r"\bnot just\b[^.!?;\n]{0,80}?\bbut\b(?: also\b)?",
    r",\s*(?:ensuring|enabling|allowing|empowering|fostering|facilitating)\b",
    r",\s*making it (?:easier|possible|simple) to\b",
    r",\s*providing a (?:seamless|smooth|robust)\b",
    r"\b(?:is|are)\s+(?:designed|intended)\s+to\s+(?:help|allow|enable|empower)\b",
    r"\bserves?\s+as\s+a\s+(?:testament|gateway|foundation|catalyst)\b",
    r"\bwhether you(?:'?re| are) a\b[^,\n]{2,40}\bor a\b",
    r"\blook no further\b",
    r"\bin an era (?:where|of)\b",
    r"\bnot\s+only\b[^.!?;\n]{0,80}?\bbut\s+(?:also\b)?",
    r"buckle up",
    r"take it to the next level",
    r"unlock the power of",
    r"supercharge your",
    r"move the needle",
    r"without further ado",
    r"as an ai(?: language)? model",
    r"i hope this helps",
    r"great question",
    r"plays? a (?:crucial|pivotal|vital|key) role",
    r"i hope this (?:email|message)?\s*finds you well",
    r"please don'?t hesitate to reach out",
    r"feel free to reach out",
    r"happy to dig deeper",
    r"let me know if you(?:'d like me to| have any questions)",
    r"^[^\S\n]*Repro:[^\S\n]*$",
    r",\s*ensuring\b",
    r",\s*so you can'?t lock yourself out\b",
    r"\b(your|our|their|its)\s+[^,;.\n]{1,35},\s+\1\s+[^,;.\n]{1,35},?\s+and\s+\1\b",
]

# Medium-risk phrases - context dependent
MEDIUM_RISK_PHRASES = [
    r"however,? it is important to",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\bin essence\b",
    r"\bessentially\b",
    r"\bfundamentally\b",
    r"\bultimately\b",
    r"\bthat being said\b",
    r"\bin conclusion\b",
    r"\bin summary\b",
    r"\bneedless to say\b",
    r"\bit goes without saying\b",
]

# Buzzwords and corporate jargon. Word-bounded and inflection-aware so that
# "leverage" doesn't also fire inside longer words, and so that overlapping
# entries ("seamless" / "seamless integration") don't double count.
BUZZWORDS = [
    r"\bsynergistic\b",
    r"\bholistic(?: approach)?\b",
    r"\bparadigm shift\b",
    r"\bgame-changer\b",
    r"\brevolutionary\b",
    r"\bcutting-edge\b",
    r"\bnext-generation\b",
    r"\bworld-class\b",
    r"\bbest-in-class\b",
    r"\bleverag(?:e|es|ed|ing)\b",
    r"\butili[sz](?:e|es|ed|ing)\b",
    r"\bempower(?:s|ed|ing|ment)?\b",
    r"\bunlock(?:s|ed|ing)? (?:the )?potential\b",
    r"\bdrive innovation\b",
    r"\bdelv(?:e|es|ing)\b",
    r"\bvibrant\b",
    r"\bpivotal\b",
    r"\bintricate\b",
    r"\bmeticulous(?:ly)?\b",
    r"\bbolster(?:ed|ing|s)?\b",
    r"\bgarner(?:ed|ing|s)?\b",
    r"\bunderscore(?:s|d)?\b",
    r"\bmultifaceted\b",
    r"\bgroundbreaking\b",
    r"\btransformative\b",
    r"\brevolutioni[sz](?:e|es|ed|ing)\b",
    r"\bseamless(?:ly)?\b",
    r"\brobust\b",
    r"\balign(?:s|ed|ing)? with\b",
    r"\bstreamline(?:s|d)?\b|\bstreamlining\b",
    r"\bfoster(?:s|ed|ing)?\b",
    r"\bspearhead(?:s|ed|ing)?\b",
    r"\bkey takeaways?\b",
    r"\bin terms of\b",
    r"\bat the heart of\b",
    r"\bfoundational\b",
    r"\binterplay\b",
    r"\bparamount\b",
]

# Japanese AI slop patterns (bureaucratic padding, conjunction chains, vague verbs, conclusion tails)
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
    r"と言っても過言ではありません",
    r"過言ではない",
    r"ことが伺えます",
    r"の一助となる",
    r"の一助となります",
    r"に他なりません",
    r"の(?:確認|実施|最適化|推進|向上|管理|徹底)を行う",
    r"の実現を図る",
    r"の実現に向けて",
    r"言うまでもなく",
    r"結論から申し上げますと",
    r"結論から言うと",
    r"極めて重要な役割を果た",
    r"特筆すべき(?:点|こと)は",
    r"お忙しいところ恐縮ですが",
    r"[^、。\n]{2,15}、[^、。\n]{2,15}、そして[^、。\n]{2,15}",
]

# Meta-commentary patterns
META_COMMENTARY = [
    r"in this (?:article|post|document|section)",
    r"as we (?:explore|examine|discuss|delve)",
    r"let'?s take a (?:closer )?look",
    r"now that we'?ve covered",
    r"before we proceed",
    r"it'?s crucial to understand",
    r"\bhow (?:it|things|permissions|\w+) works? today\b",
    r"\bhow (?:it|things|permissions|\w+) works? under the hood\b",
    r"\bsimple guide\b",
    r"\baction plan\b",
    r"\bquick(?:-start)? guide\b",
    r"\bcomprehensive guide\b",
    r"\bthis document explains\b",
    r"\bthis guide (?:walks|explains|covers)\b",
]

# Excessive hedging
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
# Named after the failure mode in IJRESM V7 I11 - synonym-swapped output
# scored 0% "AI" while the sentences stopped meaning anything.
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

# Priority order: earlier categories claim a span first, so a match is reported
# once, under the most specific label. (name, patterns, points per hit)
CATEGORIES = [
    ("high_risk", HIGH_RISK_PHRASES, 15),
    ("japanese_slop", JP_SLOP_PHRASES, 15),
    ("thesaurus", THESAURUS_TELLS, 12),
    ("meta_commentary", META_COMMENTARY, 10),
    ("medium_risk", MEDIUM_RISK_PHRASES, 8),
    ("hedging", HEDGE_WORDS, 6),
    ("buzzwords", BUZZWORDS, 5),
]
PHRASE_WEIGHTS = {name: pts for name, _, pts in CATEGORIES}
RECOMMENDATIONS = {
    "high_risk": "Replace high-risk phrases with direct, specific language",
    "japanese_slop": "Cut formulaic keigo padding and vague conclusion tails (〜と言えるでしょう)",
    "thesaurus": "Undo thesaurus swaps; the plain word was better",
    "meta_commentary": "Delete meta-commentary; lead with actual content",
    "medium_risk": "Drop filler transitions; let sentence order carry the logic",
    "hedging": "Reduce hedging; be direct and confident in statements",
    "buzzwords": "Remove buzzwords and use concrete, specific terms",
    "structure": "Restructure document to avoid generic AI patterns",
}
STRUCTURE_POINTS = 10   # flat: structural flags are document-level, not per-1000-words
MIN_SCORE_WORDS = 150   # a 30-word note must not score like a 30-word pile of buzzwords
SCORE_K = 120.0         # density (points per 1000 words) at which the phrase score hits ~63

# Quick rewrites shown next to findings. First regex that matches wins.
SUGGESTIONS = [
    (r"^,\s*(?:ensuring|enabling|allowing|empowering|fostering|facilitating)", "cut dangling participial tail; state direct result"),
    (r"^,\s*making it (?:easier|possible|simple) to", "cut participial filler; state what is changed"),
    (r"^,\s*providing a (?:seamless|smooth|robust)", "cut participial evaluation; state concrete behavior"),
    (r"^(?:is|are)\s+(?:designed|intended)\s+to", "use active verb (e.g. 'is designed to help' -> 'helps')"),
    (r"^serves?\s+as\s+a", "use direct verb (e.g. 'acts as' -> what it does)"),
    (r"^whether you(?:'?re| are) a", "cut generic audience framing"),
    (r"^look no further", "cut marketing exclamation"),
    (r"^in an era", "state the context directly"),
    (r"^not\s+only.*but", "state facts directly without false contrast"),
    (r"^と言っても過言ではありません|^過言ではない", "cut hyperbolic assertion; state concrete fact"),
    (r"^ことが伺えます", "state direct finding (e.g. '〜である')"),
    (r"^の一助となる|^の一助となります", "state concrete outcome instead of '一助'"),
    (r"^に他なりません", "state conclusion directly without double negative"),
    (r"^の(?:確認|実施|最適化|推進|向上|管理|徹底)を行う", "use direct verb (e.g. '確認する' not '確認を行う')"),
    (r"^の実現を図る|^の実現に向けて", "use direct transitive verb (e.g. '実現する')"),
    (r"^言うまでもなく", "cut filler phrase; state fact"),
    (r"^結論から(?:申し上げますと|言うと)", "lead with content directly without meta-commentary"),
    (r"^極めて重要な役割を果た", "state specific function instead of vague praise"),
    (r"^特筆すべき", "state key finding directly"),
    (r".*、.*、そして.*", "break up English-style triad (A、B、そしてC) into natural Japanese clauses"),
(r"^(?:utili[sz]|leverag)", "use"),
    (r"^in order to$", "to"),
    (r"^commence$", "start / begin"),
    (r"^endeavou?r", "try"),
    (r"^myriad of$|^plethora$", "many / a lot of / a number"),
    (r"^delve into|^dive deep into|^delv", "look at / examine / just do it"),
    (r"^unpack", "explain / break down"),
    (r"^empower", "let / help / enable"),
    (r"^streamlin", "simplify"),
    (r"^seamless", "cut it, or say what actually works smoothly"),
    (r"^robust", "say what it survives"),
    (r"^foster", "encourage / build"),
    (r"^spearhead", "lead"),
    (r"^align(?:s|ed|ing)? with", "match / fit"),
    (r"^(?:your|our|their|its)\s+.*,\s+(?:your|our|their|its)\s+", "cut possessive repetition / simplify list"),
    (r"^when it comes to", "for / with / about"),
    (r"^in the realm of", "in"),
    (r"^in terms of", "for / on / cut"),
    (r"^it(?:'s| is) (?:important|worth) (?:to )?not", "delete; state the fact"),
    (r"^(?:furthermore|moreover)$", "also / cut"),
    (r"^(?:essentially|fundamentally|ultimately|in essence)$", "cut"),
    (r"^at the end of the day", "cut, or say 'in the end'"),
    (r"^let me know if", "cut, or ask a specific question"),
    (r"^(?:feel free|please don't hesitate)", "cut"),
]
_SUGGESTIONS = [(re.compile(p, re.I), s) for p, s in SUGGESTIONS]


def _compile(patterns: List[str]) -> List[re.Pattern]:
    """Literal spaces match any whitespace run (so hard-wrapped prose still hits);
    ASCII apostrophes also match the curly one."""
    return [
        re.compile(p.replace("'", "['\u2019]").replace(" ", r"\s+"), re.IGNORECASE | re.MULTILINE)
        for p in patterns
    ]


COMPILED = {name: _compile(patterns) for name, patterns, _ in CATEGORIES}

# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #

SENTENCE_SPLIT = re.compile(r"[.!?]+[\s\"')\]]+|[\u3002\uff01\uff1f]+|\n{2,}")
ABBREVIATION = re.compile(r"\b(?:e\.g|i\.e|vs|cf|Dr|Mr|Mrs|Ms|Prof|Inc|approx)\.", re.IGNORECASE)
CONTRACTION = re.compile(r"\b\w+['\u2019](?:t|s|re|ve|ll|d|m)\b", re.IGNORECASE)

# Participles that don't end in -ed/-en, and -en/-ed words that aren't participles
# ("is often", "was even", "is a need"). Without these the passive count is inflated.
_IRREGULAR = ("built|made|done|held|kept|sent|found|led|left|lost|paid|told|brought|"
              "bought|caught|understood|shown|known|grown|thrown|drawn|worn")
_NOT_PARTICIPLE = ("often|even|open|then|when|between|seven|eleven|green|children|women|"
                   "kitchen|garden|token|screen|golden|wooden|sudden|need|speed|indeed|"
                   "seed|feed|hundred")
PASSIVE = re.compile(
    rf"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?(?!(?:{_NOT_PARTICIPLE})\b)"
    rf"(?:\w{{2,}}(?:ed|en)|{_IRREGULAR})\b",
    re.IGNORECASE,
)
TRIAD = re.compile(r"\b(?:\w+\s+){0,4}\w+,\s+(?:\w+\s+){0,4}\w+,?\s+and\s+(?:\w+\s+){0,4}\w+\b")
# Letters only (Unicode-aware, no digits or underscores). Apostrophes count only
# between letters, so a leading quote mark doesn't split "'all" from "all".
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*")
DIGIT_OR_SYMBOL = re.compile(r"[0-9%$&#@*/+=<>]")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")

BULLET = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]+", re.MULTILINE)
BOLD_BULLET = re.compile(
    r"^[ \t]*(?:[-*+]|\d+\.)[ \t]+(?:\*\*[^*\n]+:\*\*|\*\*[^*\n]+\*\*[ \t]*[:\u2014\u2013-])", re.MULTILINE)
EMOJI_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]+.*[\U0001F300-\U0001FAFF\u2600-\u27BF]", re.MULTILINE)
TRANSITION_START = re.compile(
    r"(?:however|furthermore|moreover|additionally|nevertheless|consequently|therefore)\b", re.IGNORECASE)

# Auxiliaries and modals. AI prose leans on these; the effect is one of the
# stronger separators reported in the German-theses study.
AUXILIARIES = {
    "is", "are", "was", "were", "be", "been", "being", "am",
    "has", "have", "had", "do", "does", "did",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
}

# Length-normalized vocabulary window. Type-token ratio falls as text grows, so
# comparing a 200-word note to a 2000-word doc without windowing is meaningless.
TTR_WINDOW = 200

# Detection studies put reliable separation at 300+ words. Under that, treat
# every rhythm number as noise rather than signal.
CONFIDENCE_FLOOR_WORDS = 300

# Above this share of CJK letters, whitespace "words" mean nothing and the
# English rhythm metrics would be garbage. Phrase checks still run.
CJK_RHYTHM_CUTOFF = 0.30

# Heuristic starting points, not measurements. Replace with your own numbers
# via `--learn` - a profile beats a guessed constant.
DEFAULT_PROFILE = {
    "burstiness": 0.55,      # coefficient of variation of sentence length
    "em_dash_per_500w": 1.0,
    "contractions_per_100w": 1.5,
    "passive_per_100w": 2.0,
    "triads_per_1000w": 4.0,
    "max_parataxis_run": 2,  # consecutive short simple sentences
    "max_opener_run": 2,     # consecutive sentences opening with the same word
    "type_token_ratio": 0.62,
    "hapax_ratio": 0.52,
    "repeated_trigram_ratio": 0.03,
    "aux_per_100w": 9.0,
    "digit_symbol_per_100w": 3.0,
}

PROFILE_PATH = Path.home() / ".claude" / "voice-profile.json"


def strip_markup(text: str) -> str:
    """Reduce a document to its prose. Tables, frontmatter, and code are data, not sentences."""
    text = re.sub(r"\A---\n.*?\n---\n", " ", text, flags=re.DOTALL)   # YAML frontmatter
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)           # HTML comments
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)                  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)               # links keep their label
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^\s*\|.*$", "", text, flags=re.MULTILINE)          # table rows
    text = re.sub(r"^\s*#{1,6}\s+.*$", "", text, flags=re.MULTILINE)   # headings are labels
    text = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)            # emphasis markers aren't symbols
    return text


def mask_code(text: str) -> str:
    """Blank out code spans but keep every offset and newline, so phrase matches
    keep correct line numbers and documented examples don't count as slop."""
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group())
    text = re.sub(r"```.*?```", blank, text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", blank, text)


def split_sentences(prose: str) -> List[str]:
    prose = ABBREVIATION.sub(lambda m: m.group().replace(".", ""), prose)
    return [s.strip() for s in SENTENCE_SPLIT.split(prose) if s and s.strip()]


def sentences(text: str) -> List[str]:
    return split_sentences(strip_markup(text))


def tokenize(prose: str) -> List[str]:
    return WORD.findall(prose.lower().replace("\u2019", "'"))


def word_count(text: str) -> int:
    """Whitespace words for Latin text, plus roughly half a word per CJK character."""
    return len(CJK.sub(" ", text).split()) + len(CJK.findall(text)) // 2


def cjk_share(text: str) -> float:
    letters = sum(1 for c in text if c.isalpha())
    return len(CJK.findall(text)) / letters if letters else 0.0


def max_opener_run(sents: List[str]) -> int:
    """Longest run of consecutive sentences that open with the same word."""
    best = run = 0
    prev = None
    for s in sents:
        m = WORD.search(s.lower())
        first = m.group() if m else None
        run = run + 1 if (first and first == prev) else 1
        prev = first
        best = max(best, run)
    return best


def measure(text: str, ignore: frozenset | set = frozenset()) -> Dict[str, float]:
    """Structural fingerprint of a piece of prose. Same shape for text and profile.

    Everything is computed from the markup-stripped prose, so code blocks, tables
    and URLs can't skew the per-word rates."""
    prose = strip_markup(text)
    words = prose.split()
    wc = max(len(words), 1)
    sents = split_sentences(prose)
    lengths = [len(s.split()) for s in sents] or [0]
    mean_len = statistics.fmean(lengths)

    # Parataxis: longest run of consecutive short sentences with no subordination.
    run = best_run = 0
    for s in sents:
        n = len(s.split())
        if n <= 8 and not re.search(r"[,;:]|\b(?:because|although|while|which|so that)\b", s):
            run += 1
            best_run = max(best_run, run)
        else:
            run = 0

    toks = [t for t in tokenize(prose) if t not in ignore]
    return {
        "words": len(words),
        "sentences": len(sents),
        "mean_sentence_len": round(mean_len, 2),
        "burstiness": round(statistics.pstdev(lengths) / mean_len, 3) if mean_len else 0.0,
        "em_dash_per_500w": round(prose.count("\u2014") / wc * 500, 2),
        "contractions_per_100w": round(len(CONTRACTION.findall(prose)) / wc * 100, 2),
        "passive_per_100w": round(len(PASSIVE.findall(prose)) / wc * 100, 2),
        "triads_per_1000w": round(len(TRIAD.findall(prose)) / wc * 1000, 2),
        "max_parataxis_run": best_run,
        "max_opener_run": max_opener_run(sents),
        "type_token_ratio": windowed_ttr(toks),
        "hapax_ratio": hapax_ratio(toks),
        "repeated_trigram_ratio": repeated_trigram_ratio(toks),
        "aux_per_100w": round(sum(t in AUXILIARIES for t in toks) / wc * 100, 2),
        "digit_symbol_per_100w": round(
            sum(bool(DIGIT_OR_SYMBOL.search(w)) for w in words) / wc * 100, 2
        ),
    }


def find_typos(toks: List[str]) -> set:
    """Rare tokens that sit within a small edit distance of a frequent one.

    Misspellings are each unique, so counting them as vocabulary inflates both
    type-token and hapax ratio. No spellchecker is installed and no system word
    list exists, so the corpus supplies its own dictionary: words the author
    uses repeatedly are correct by definition, and near-misses of those are not.
    """
    counts = Counter(toks)
    freq_set = {w for w, c in counts.items() if c >= 5 and len(w) > 3}

    typos = set()
    for w, c in counts.items():
        if c > 1 or len(w) <= 3:
            continue
        # Exact edit-distance-1 first. Transpositions ("tihs", "fiel") only score
        # about 0.75 on difflib, below any cutoff loose enough to stay precise.
        hits = edits1(w) & freq_set
        # A one-edit difference at the tail is inflection, not error: "aborts"
        # against "abort", "commits" against "commit". Real typos diverge earlier.
        if any(len(os.path.commonprefix([w, m])) < len(w) - 1 for m in hits):
            typos.add(w)
    return typos


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


def windowed_ttr(toks: List[str]) -> float:
    """Vocabulary richness, averaged over fixed windows so length doesn't skew it."""
    if not toks:
        return 0.0
    windows = [toks[i:i + TTR_WINDOW] for i in range(0, len(toks), TTR_WINDOW)]
    if len(windows) > 1 and len(windows[-1]) < TTR_WINDOW // 2:
        windows.pop()
    return round(statistics.fmean(len(set(w)) / len(w) for w in windows), 3)


def hapax_ratio(toks: List[str]) -> float:
    """Share of vocabulary used exactly once. Falls when a text keeps recycling words."""
    if not toks:
        return 0.0
    counts = Counter(toks)
    return round(sum(1 for c in counts.values() if c == 1) / len(counts), 3)


def repeated_trigram_ratio(toks: List[str]) -> float:
    """Share of word trigrams appearing more than once - flat n-gram distribution."""
    if len(toks) < 4:
        return 0.0
    counts = Counter(zip(toks, toks[1:], toks[2:]))
    return round(sum(1 for c in counts.values() if c > 1) / len(counts), 3)


def load_profile(path: Path = PROFILE_PATH) -> Tuple[Dict[str, float], str]:
    """Load a learned profile, filling any missing keys from the defaults so a
    profile written by an older version doesn't crash the newer checks."""
    if path.exists():
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))["profile"]
            return {**DEFAULT_PROFILE, **stored}, str(path)
        except (json.JSONDecodeError, KeyError, TypeError, OSError) as e:
            print(f"warning: could not read profile {path} ({e.__class__.__name__}); "
                  f"using defaults", file=sys.stderr)
    return dict(DEFAULT_PROFILE), "built-in defaults (run --learn for your own)"


# Metrics the medium dictates rather than the author. Chat prompts are fragments
# with no punctuation, so learning these from a chat corpus teaches the wrong
# lesson: "write emails in fragments". Learn them from real prose or not at all.
# Verb-dependent rates belong here too: fragments have few finite verbs, so a
# chat corpus reports near-zero passives and auxiliaries regardless of the author.
MEDIUM_BOUND = {
    "burstiness", "max_parataxis_run", "max_opener_run", "contractions_per_100w",
    "repeated_trigram_ratio", "passive_per_100w", "aux_per_100w", "triads_per_1000w",
}


def is_fragmentary(metrics: Dict[str, float]) -> bool:
    return metrics["mean_sentence_len"] < 12 or metrics["max_parataxis_run"] > 6


def learn(sample_paths: List[str], out: Path = PROFILE_PATH) -> Dict:
    """Build a voice profile from writing you actually wrote."""
    bodies, used = [], []
    for p in sample_paths:
        try:
            body = Path(p).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"skip {p}: {e}", file=sys.stderr)
            continue
        if len(body.split()) < 30:
            print(f"skip {p}: under 30 words, too short to be signal", file=sys.stderr)
            continue
        bodies.append(body)
        used.append(p)

    if not bodies:
        raise SystemExit("No usable samples. Need files of 30+ words that you wrote.")

    # Typos are found across the whole corpus, not per file: a word has to recur
    # somewhere to prove it isn't a slip, and one file may be too small to show that.
    typos = find_typos(tokenize(strip_markup("\n".join(bodies))))
    per_sample = [measure(b, ignore=typos) for b in bodies]

    # Run-length metrics take the worst case you naturally produce; rates take the median.
    profile = {}
    for k in DEFAULT_PROFILE:
        vals = [m[k] for m in per_sample]
        profile[k] = max(vals) if k.startswith("max_") else round(statistics.median(vals), 3)
    profile["mean_sentence_len"] = round(statistics.median(m["mean_sentence_len"] for m in per_sample), 2)

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
        "sources": [Path(p).name for p in used],
        "fragmentary_corpus": fragmentary,
        "defaulted_metrics": dropped,
        "typos_excluded": len(typos),
        "typo_sample": sorted(typos)[:15],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def suggest(match: str) -> Optional[str]:
    norm = " ".join(match.lower().replace("\u2019", "'").split())
    for rx, hint in _SUGGESTIONS:
        if rx.search(norm):
            return hint
    return None


def excerpt(line: str, col: int, width: int = 70) -> str:
    """A window of the line around the match, not just its first 60 characters."""
    start = max(0, col - width // 3)
    end = min(len(line), start + width)
    return ("\u2026" if start > 0 else "") + line[start:end].strip() + ("\u2026" if end < len(line) else "")


class SlopDetector:
    def __init__(self, filepath: str, profile: Optional[Dict[str, float]] = None,
                 profile_src: str = "", text: Optional[str] = None):
        self.filepath = Path(filepath)
        self.text = text if text is not None else self._load_file()
        self.lines = self.text.split("\n")
        self.profile = {**DEFAULT_PROFILE, **(profile or {})}
        self.profile_src = profile_src or "built-in defaults"
        self.is_prose = self.filepath.suffix.lower() in PROSE_EXTS
        self._reset()

    def _reset(self):
        """analyze() is idempotent: calling it twice must not double the findings."""
        self.findings: Dict[str, List[Dict]] = defaultdict(list)
        self.metrics: Dict[str, float] = {}
        self.deviations: List[Dict] = []
        self.notes: List[str] = []
        self.low_confidence = False

    def _load_file(self) -> str:
        with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    # ----------------------------------------------------------------- phrases

    def _scan_phrases(self):
        """Scan the whole text (so phrases wrapped across lines still match), skip
        code spans in prose files, and report each span once under the highest-
        priority category that claims it."""
        scan = mask_code(self.text) if self.is_prose else self.text
        starts = [0] + [m.end() for m in re.finditer("\n", scan)]
        claimed = bytearray(len(scan))

        for category, _, _ in CATEGORIES:
            for rx in COMPILED[category]:
                for m in rx.finditer(scan):
                    s, e = m.span()
                    if e == s or any(claimed[s:e]):
                        continue
                    claimed[s:e] = b"\x01" * (e - s)
                    line_no = bisect_right(starts, s)
                    col = s - starts[line_no - 1]
                    raw = self.lines[line_no - 1] if line_no <= len(self.lines) else ""
                    match = " ".join(m.group().split())
                    self.findings[category].append({
                        "line": line_no,
                        "text": raw.strip(),
                        "match": match,
                        "position": col,
                        "excerpt": excerpt(raw, col),
                        "hint": suggest(match),
                    })
            self.findings[category].sort(key=lambda f: (f["line"], f["position"]))

    # --------------------------------------------------------------- analysis

    def analyze(self) -> Dict:
        """Run all analyses and return findings."""
        self._reset()
        self._scan_phrases()
        self._analyze_structure()

        if self.is_prose:
            if cjk_share(self.text) > CJK_RHYTHM_CUTOFF:
                self.notes.append("Mostly CJK text: rhythm metrics skipped (they assume space-separated words).")
            else:
                self._analyze_rhythm()

        score = self._calculate_slop_score()
        findings = {name: self.findings.get(name, []) for name, _, _ in CATEGORIES}
        findings["structure"] = self.findings.get("structure", [])

        return {
            "file": str(self.filepath),
            "findings": findings,
            "counts": {k: len(v) for k, v in findings.items()},
            "score": score,
            "metrics": self.metrics,
            "deviations": self.deviations,
            "low_confidence": self.low_confidence,
            "hot_lines": self._hot_lines(),
            "notes": self.notes,
            "summary": self._generate_summary(score),
        }

    def _analyze_rhythm(self):
        """Measure the structural signals the phrase list can't see."""
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
             "too few contractions - 'don't' not 'do not'"),
            # Floors matter: a profile that legitimately measures 0.0 would
            # otherwise flag every single occurrence as a deviation.
            ("passive_per_100w", "above", max(p["passive_per_100w"] * 1.6, 1.5),
             "passive voice pile-up - name who does the thing"),
            ("triads_per_1000w", "above", max(p["triads_per_1000w"] * 1.6, 2.0),
             "rule-of-three habit - use two items, or four"),
            ("max_parataxis_run", "above", p["max_parataxis_run"],
             "parataxis - short declaratives in a row, connect them"),
            ("max_opener_run", "above", p["max_opener_run"],
             "same opening word on consecutive sentences - vary the entry point"),
            ("type_token_ratio", "below", p["type_token_ratio"] * 0.85,
             "thin vocabulary - same words recycled"),
            ("hapax_ratio", "below", p["hapax_ratio"] * 0.85,
             "few words used once - reach past the first word that comes to mind"),
            ("repeated_trigram_ratio", "above", max(p["repeated_trigram_ratio"] * 1.5, 0.02),
             "repeated phrasing - flat n-gram spread, the clearest machine tell"),
            ("aux_per_100w", "above", max(p["aux_per_100w"] * 1.4, 8.0),
             "auxiliary verb pile-up - use verbs that do something"),
            ("digit_symbol_per_100w", "above", max(p["digit_symbol_per_100w"] * 2.5, 12.0),
             "numbers and symbols dense enough to read as formulaic"),
        ]
        for key, direction, limit, advice in checks:
            actual = self.metrics[key]
            if (direction == "below" and actual < limit) or (direction == "above" and actual > limit):
                self.deviations.append({
                    "metric": key, "actual": actual,
                    "limit": round(limit, 3), "direction": direction, "advice": advice,
                })

    def _analyze_structure(self):
        """Document-level patterns: opening meta-commentary, transition pile-ups,
        and the formatting habits chat models default to."""
        body = mask_code(self.text) if self.is_prose else self.text

        head = " ".join(body.split())[:400]
        if re.search(r"\bin this [^.]{1,60}? (?:will|we)\b", head, re.IGNORECASE):
            self.findings["structure"].append({
                "issue": "Opening meta-commentary",
                "description": "Document starts with meta-commentary instead of content",
            })

        # Per paragraph, not per line (the old message said paragraphs but counted
        # lines), and only with enough paragraphs for a ratio to mean something.
        paras = [p.strip() for p in re.split(r"\n\s*\n", body)
                 if p.strip() and not p.lstrip().startswith("#")]
        if len(paras) >= 4:
            hits = sum(bool(TRANSITION_START.match(p)) for p in paras)
            if hits / len(paras) > 0.3:
                self.findings["structure"].append({
                    "issue": "Excessive transitions",
                    "description": f"{hits / len(paras):.0%} of paragraphs start with transition words",
                })

        if self.is_prose:
            bullets, bold = len(BULLET.findall(body)), len(BOLD_BULLET.findall(body))
            if bullets >= 4 and bold / bullets > 0.5:
                self.findings["structure"].append({
                    "issue": "Bold-label bullets",
                    "description": f"{bold}/{bullets} bullets open with a **bold label:** - the chat-model list template",
                })
            emoji = len(EMOJI_HEADING.findall(body))
            if emoji >= 2:
                self.findings["structure"].append({
                    "issue": "Emoji headings",
                    "description": f"{emoji} headings carry emoji",
                })

    def _hot_lines(self, top: int = 5) -> List[Dict]:
        """Lines carrying the most weighted phrase hits — the best place to start editing."""
        weights = PHRASE_WEIGHTS
        per_line: Dict[int, Dict] = {}
        for key, items in self.findings.items():
            if key not in weights:
                continue
            for f in items:
                entry = per_line.setdefault(f["line"], {"line": f["line"], "weight": 0,
                                                        "matches": [], "text": f.get("text", "")})
                entry["weight"] += weights[key]
                entry["matches"].append(f["match"])
        ranked = sorted(per_line.values(), key=lambda e: (-e["weight"], e["line"]))
        return [e for e in ranked if len(e["matches"]) > 1][:top]

    def _calculate_slop_score(self) -> int:
        """Overall slop score (0-100, higher is worse).

        Phrase points become a density per 1000 words (with a word floor so tiny
        files aren't hypersensitive) and pass through a saturating curve, so the
        score climbs steadily instead of slamming into the cap. Structural flags
        and rhythm deviations are document-level and are added flat afterwards.
        """
        points = sum(len(self.findings.get(cat, [])) * w for cat, w in PHRASE_WEIGHTS.items())
        density = points / max(word_count(self.text), MIN_SCORE_WORDS) * 1000
        score = 100 * (1 - math.exp(-density / SCORE_K))

        score += STRUCTURE_POINTS * len(self.findings.get("structure", []))
        per_deviation = 4 if self.low_confidence else 9
        score += min(len(self.deviations) * per_deviation, 45)
        return min(int(round(score)), 100)

    def _generate_summary(self, score: int) -> str:
        if score < 20:
            return "\u2705 Low slop detected - Writing appears authentic and purposeful"
        elif score < 40:
            return "\u26a0\ufe0f  Moderate slop detected - Some generic patterns present"
        elif score < 60:
            return "\U0001F6A8 High slop detected - Many AI-generated patterns found"
        return "\U0001F480 Severe slop detected - Document heavily relies on generic AI patterns"

    # ----------------------------------------------------------------- report

    SECTIONS = [
        ("high_risk", "\U0001F534 HIGH-RISK PHRASES", 5),
        ("medium_risk", "\U0001F7E0 MEDIUM-RISK PHRASES", 5),
        ("meta_commentary", "\U0001F4DD META-COMMENTARY", 3),
        ("thesaurus", "\U0001F500 HUMANIZER TELLS (thesaurus-swapped wording: evades detectors, reads worse)", 5),
        ("japanese_slop", "\U0001F1EF\U0001F1F5 JAPANESE AI SLOP TELLS", 5),
        ("hedging", "\U0001F914 EXCESSIVE HEDGING", 3),
    ]

    @staticmethod
    def _fmt(item: Dict) -> str:
        hint = f"  \u2192 {item['hint']}" if item.get("hint") else ""
        return f"  Line {item['line']}: '{item['match']}'{hint}\n      {item['excerpt']}"

    def print_report(self, verbose: bool = False, results: Optional[Dict] = None):
        """Print a formatted report of findings."""
        results = results or self.analyze()
        findings = results["findings"]

        print(f"\n{'=' * 70}")
        print(f"AI Slop Detection Report: {self.filepath.name}")
        print(f"{'=' * 70}\n")
        print(f"Overall Slop Score: {results['score']}/100")
        print(f"Assessment: {results['summary']}\n")
        for note in results["notes"]:
            print(f"  note: {note}\n")

        for key, title, limit in self.SECTIONS:
            items = findings.get(key, [])
            if not items:
                continue
            print(f"{title} ({len(items)} found):")
            shown = items if verbose else items[:limit]
            for item in shown:
                print(self._fmt(item))
            if len(shown) < len(items):
                print(f"  ... and {len(items) - len(shown)} more (use -v)")
            print()

        if findings.get("buzzwords"):
            items = findings["buzzwords"]
            print(f"\U0001F4E2 BUZZWORDS & JARGON ({len(items)} found):")
            if verbose:
                for item in items:
                    print(self._fmt(item).split("\n")[0])
            else:
                top = Counter(i["match"].lower() for i in items).most_common(10)
                print("  " + ", ".join(f"{w} \u00d7{n}" if n > 1 else w for w, n in top))
                extra = len({i["match"].lower() for i in items}) - len(top)
                if extra > 0:
                    print(f"  ... and {extra} more unique buzzwords")
            print()

        if findings.get("structure"):
            print("\U0001F3D7\ufe0f  STRUCTURAL ISSUES:")
            for f in findings["structure"]:
                print(f"  \u2022 {f['issue']}: {f['description']}")
            print()

        if results["deviations"]:
            note = " - under 300 words, treat as weak signal" if results["low_confidence"] else ""
            print(f"\U0001F39A\ufe0f  VOICE DEVIATION (vs {self.profile_src}){note}:")
            for d in results["deviations"]:
                arrow = "\u2193" if d["direction"] == "below" else "\u2191"
                print(f"  {arrow} {d['metric']}: {d['actual']} (limit {d['limit']}) - {d['advice']}")
            print()
        elif self.is_prose and results["metrics"].get("sentences", 0) >= 4:
            print(f"\U0001F39A\ufe0f  Voice: within profile ({self.profile_src})\n")

        if results["score"] > 20:
            print("\U0001F4A1 RECOMMENDATIONS:")
            tips = [
                ("high_risk", "Replace high-risk phrases with direct, specific language"),
                ("medium_risk", "Cut filler connectives (furthermore, essentially, ultimately)"),
                ("buzzwords", "Remove buzzwords and use concrete, specific terms"),
                ("meta_commentary", "Delete meta-commentary; lead with actual content"),
                ("hedging", "Reduce hedging; be direct and confident in statements"),
                ("thesaurus", "Undo synonym swaps; plain words beat rare ones"),
                ("structure", "Restructure the document to avoid generic AI patterns"),
            ]
            for key, tip in tips:
                if findings.get(key):
                    print(f"  \u2022 {tip}")
            if results["deviations"]:
                print("  \u2022 Rework rhythm: vary sentence length and openers, prefer active verbs")
            print()


def selftest():
    """Runnable checks: flat AI-shaped prose must outscore varied human-shaped prose,
    plus regression checks for each behaviour that has bitten before."""
    flat = (
        "The system is designed to be scalable. The system is built to be robust. "
        "The system is made to be fast. Data is processed by the engine. Results are "
        "returned to the user. Errors are handled by the framework. It is important "
        "to note that performance is considered to be good.\n"
    )
    varied = (
        "Scaling wasn't the hard part; the retry loop was. I spent two days convinced "
        "the queue was dropping jobs, and it wasn't. The worker restarted mid-batch and "
        "nobody had written down what that meant for in-flight rows, so I found out the "
        "expensive way, at 2am, with a half-migrated table and no rollback plan.\n"
    )

    def run(body: str, name: str = "x.md") -> Dict:
        return SlopDetector(name, text=body).analyze()

    flat_r, varied_r = run(flat), run(varied)
    assert flat_r["score"] > varied_r["score"], (flat_r["score"], varied_r["score"])
    assert flat_r["metrics"]["burstiness"] < varied_r["metrics"]["burstiness"]
    assert any(d["metric"] == "passive_per_100w" for d in flat_r["deviations"])
    assert any(d["metric"] == "max_opener_run" for d in flat_r["deviations"])
    assert flat_r["counts"]["high_risk"] >= 1  # "It is important to note that"
    assert measure("Don't. It's fine.")["contractions_per_100w"] > 0
    assert measure("Don\u2019t. It\u2019s fine.")["contractions_per_100w"] > 0

    # Typo filter
    corpus = "this is the prompt and the review this prompt again review the file commit branch " * 8
    typos = find_typos(WORD.findall((corpus + " tihs promnpt reveiw fiel comit brnach").lower()))
    assert typos == {"tihs", "promnpt", "reveiw", "fiel", "comit", "brnach"}, typos
    assert not find_typos(WORD.findall((corpus + " orthogonal idempotent hysteresis").lower()))

    # Phrases wrapped across lines, and curly apostrophes, still match
    assert run("We will delve\ninto the data.")["counts"]["high_risk"] == 1
    assert run("It\u2019s important to note that this works.")["counts"]["high_risk"] == 1
    # Reported line number is the line where the match starts
    assert run("one\ntwo\nWe delve into it.")["findings"]["high_risk"][0]["line"] == 3
    # Code is not prose
    assert run("Use `delve into` here.\n```\nutilize leverage\n```\n")["score"] == 0
    # Overlapping patterns count once, under the most specific label
    r = run("We delve into it.")
    assert r["counts"]["high_risk"] == 1 and r["counts"]["buzzwords"] == 0, r["counts"]
    assert run("The seamless integration works.")["counts"]["buzzwords"] == 1
    # Bounded "not just ... but": no match across sentences
    assert run("It is not just fast. Later we saw the but.")["counts"]["high_risk"] == 0
    # Passive false positives
    assert measure("It is often true. It was even open. We need it.")["passive_per_100w"] == 0
    # Robustness: empty file and whitespace-only file
    assert run("")["score"] == 0 and run("\n\n  \n")["score"] == 0
    # analyze() is idempotent
    d = SlopDetector("x.md", text="We delve into it.")
    assert d.analyze()["score"] == d.analyze()["score"]
    # Short text is not hypersensitive
    assert run("Feel free to reach out.")["score"] < 60

    # English grammatical tells: participial claws, copular stacking, false contrast
    assert run("The daemon runs locally, ensuring low latency.")["counts"]["high_risk"] >= 1
    assert run("This module is designed to allow fast builds.")["counts"]["high_risk"] >= 1
    assert run("It is not only fast but also secure.")["counts"]["high_risk"] >= 1
    assert run("Whether you are a novice or a senior engineer, this works.")["counts"]["high_risk"] >= 1

    # Japanese grammatical tells: speculative tails, nominalizations, triad soshite
    assert run("これは革新的と言っても過言ではありません。")["counts"]["japanese_slop"] >= 1
    assert run("ログから正常に動作していることが伺えます。")["counts"]["japanese_slop"] >= 1
    assert run("業務効率化の一助となるでしょう。")["counts"]["japanese_slop"] >= 1
    assert run("定期的な設定の確認を行う。")["counts"]["japanese_slop"] >= 1
    assert run("安全性、信頼性、そして高速性を兼ね備えています。")["counts"]["japanese_slop"] >= 1
    # CJK: phrase checks run, rhythm skipped
    jp = run("ご確認のほどよろしくお願いいたします。" * 3)
    assert jp["counts"]["japanese_slop"] == 3 and not jp["metrics"]
    # Structure: bold-label bullet template
    tpl = "\n".join(f"- **Point {i}:** something" for i in range(5))
    assert any(f["issue"] == "Bold-label bullets" for f in run(tpl)["findings"]["structure"])

    print(f"selftest ok - flat={flat_r['score']} varied={varied_r['score']}, all regression checks pass")


def collect_files(args: List[str]) -> List[str]:
    """Expand directories to their prose files; '-' means stdin."""
    out = []
    for a in args:
        p = Path(a)
        if a != "-" and p.is_dir():
            out.extend(
                str(f) for f in sorted(p.rglob("*"))
                if f.is_file() and f.suffix.lower() in SCAN_EXTS
                and not any(part.startswith(".") for part in f.relative_to(p).parts)
            )
        else:
            out.append(a)
    return out


def main():
    ap = argparse.ArgumentParser(description="Detect AI slop and voice drift in text.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("files", nargs="*", metavar="FILE",
                    help="files or directories to analyze; '-' reads stdin")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--learn", nargs="+", metavar="SAMPLE",
                    help="build a voice profile from writing you actually wrote")
    ap.add_argument("--profile", type=Path, default=PROFILE_PATH,
                    help=f"voice profile path (default {PROFILE_PATH})")
    ap.add_argument("--no-profile", action="store_true",
                    help="ignore the learned profile, use built-in defaults")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-above", "--fail-over", dest="fail_threshold", type=int, metavar="N",
                    help="exit 1 if any file scores above N (for CI / pre-commit)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return

    if args.learn:
        payload = learn(args.learn, args.profile)
        print(f"Voice profile written: {args.profile}")
        print(f"  {payload['samples']} samples, {payload['total_words']} words")
        for k, v in payload["profile"].items():
            tag = "  (default, corpus too fragmentary)" if k in payload["defaulted_metrics"] else ""
            print(f"  {k}: {v}{tag}")
        if payload["typos_excluded"]:
            print(f"\n  {payload['typos_excluded']} misspellings excluded from vocabulary "
                  f"metrics, e.g. {', '.join(payload['typo_sample'][:8])}")
        if payload["fragmentary_corpus"]:
            print("\n  Corpus reads as chat or notes, not prose. Sentence rhythm and "
                  "contraction habits were left at defaults;\n  add longer prose you wrote "
                  "to learn those too.")
        return

    if not args.files:
        ap.error("give a file, or --learn SAMPLE...")

    if args.no_profile:
        profile, src = dict(DEFAULT_PROFILE), "built-in defaults"
    else:
        profile, src = load_profile(args.profile)

    files = collect_files(args.files)
    if not files:
        ap.error("no analyzable files found")

    runs, had_error = [], False
    for path in files:
        try:
            if path == "-":
                det = SlopDetector("<stdin>", profile, src, text=sys.stdin.read())
            else:
                det = SlopDetector(path, profile, src)
        except OSError as e:
            print(f"skip {path}: {e}", file=sys.stderr)
            had_error = True
            continue
        runs.append((det, det.analyze()))

    if args.json:
        payload = [r for _, r in runs]
        single = len(files) == 1 and len(payload) == 1
        print(json.dumps(payload[0] if single else payload, indent=2, ensure_ascii=False))
    else:
        for det, res in runs:
            det.print_report(verbose=args.verbose, results=res)
        if len(runs) > 1:
            print(f"{'=' * 70}\nSUMMARY\n{'=' * 70}")
            for _, res in sorted(runs, key=lambda x: -x[1]["score"]):
                print(f"  {res['score']:>3}/100  {res['file']}")
            print()

    if args.fail_threshold is not None and any(r["score"] > args.fail_threshold for _, r in runs):
        sys.exit(1)
    if had_error and not runs:
        sys.exit(2)


if __name__ == "__main__":
    main()
