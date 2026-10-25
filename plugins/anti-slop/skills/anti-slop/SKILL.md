---
name: anti-slop
description: Produces human-sounding text and detects/removes AI slop across text, code, and design. Activates on any writing or drafting task (emails, docs, READMEs, PRs, messages, copy, blog posts) to prevent detectable AI patterns, or during review/cleanup to measure prose against a learned voice profile, score text via detector scripts, and strip slop. Use when the user says "write", "draft", "rewrite", "make this sound human", "anti-slop", "audit slop", "clean slop", or "check my writing".
---

# Anti-Slop: Generation, Measurement, and Cleanup

Unified toolkit for natural, human prose and clean code/design. Governs three phases:
1. **Generation:** Active constraints before writing (rhythm, syntax, vocabulary, banned words).
2. **Measurement:** Statistical detection (`detect_slop.py`), scoring (0-100), and personalized voice profiling (`--learn`).
3. **Cleanup:** Mechanical stripping (`clean_slop.py`) and code/design anti-slop audits.

---

## The Target Is Not The Detector

Write text that is genuinely the author's. Do not optimize for an AI classifier score.

Fiedler and Döpke (2025) tested 63 lecturers against 200-300 word excerpts: 57% accuracy on AI text, 64% on human text. Machine detectors performed no better. Professional-quality AI writing fooled over 80% of evaluators. Free detectors flag real human writing at a 27.2% false-positive rate (Popkov & Barrett).

Optimizing for a 0% detector score leads to the "humanizer" trap: swapping synonyms into unnatural words ("feline sprang" for "cat leapt"), injecting fake typos, or round-trip back-translating.

**Never do any of these:**
- Thesaurus swaps that reduce clarity (cat → feline, use → utilize, start → commence).
- Planted typos or grammar errors. Real error is an accidental byproduct, never a costume.
- Back-translation or round-trip paraphrasing to launder phrasing.
- Manufactured negativity or synthetic cynicism.

Write with authentic substance and clear structure. The statistical signals follow naturally.

---

## Phase 1: Generation Directives

Apply these constraints to every email, doc, PR description, README, commit message, and article.

### Pre-Writing Checks
1. Load banned vocabulary and phrases from [references/banned-words.md](references/banned-words.md). Never use items from this list.
2. Check for a learned voice profile at `~/.claude/voice-profile.json` (created via `python scripts/detect_slop.py --learn`). Match measured mean sentence length, burstiness, contraction rate, and passive rate rather than generic defaults.
3. For sentence construction, apply [references/sentence-patterns.md](references/sentence-patterns.md): main fact first, colon frames, long-then-short rhythm, semicolons for claim-and-evidence and action chains.

### Structural Rules
- **No Rule of Three:** LLMs default to triples. Break the pattern: use two, four, one, or five.
- **No uniform sentence length:** Never write three consecutive sentences of similar word count. Vary 4-word punchy sentences with 25+ word compound sentences.
- **No parataxis:** Do not chain short blunt declarative sentences in a row ("Short sentence. Then another. Then another."). Connect related thoughts using conjunctions, subordinate clauses, commas, or semicolons.
- **Complete sentences only:** A sentence carries a subject and a main verb. Punch fragments are slop even when they scan well: "Generation got cheap. Maintenance didn't." pairs a compressed sentence with one that is not a sentence at all. Verbless emphasis lines are the same move ("No logs. No metrics."). If the thought matters, give it a verb; if it doesn't, cut it. The detector flags both shapes ("Dangling auxiliary", "Verbless fragment").
- **No hedging seesaw:** Pick a side and state it plainly. Acknowledge counterpoints in one sentence max without equal weighting.
- **No corporate pep talk:** Write like an experienced practitioner including frustrations and trade-offs. No cheerleading.
- **No uniform paragraph structure:** Do not repeat topic sentence → explanation → example → transition. Vary paragraph starters and lengths. Let some end abruptly without a summary.
- **No excessive bullets:** Use sparingly. Never more than 5-7 items. If it fits in running prose, use prose.
- **No credential openers:** Avoid "As a [role], I...". State the point directly.
- **No passive construction:** Avoid "is being done", "was found to be", "are considered to be". Write active voice: name who does what.
- **Don't recycle vocabulary:** Human prose has high lexical diversity (hapax legomena). If a distinctive word was used, do not repeat it; reach for a fresh term or restructure.
- **Cut auxiliary verbs:** Cut excessive "is", "are", "was", "has been", "will be". Use active verbs that perform actions.
- **Load-bearing numbers only:** Dense figures read like machine generation unless each number carries essential weight.

### Punctuation Rules
- **Em dashes:** Maximum 1 per 500 words. Replace with commas, colons, parentheses, or periods.
- **Exclamation marks:** Maximum 1 per 1,000 words.
- **Ellipses:** Maximum 1 per piece, only when genuinely trailing off. Never as a transition.
- **Semicolons & colons:** Use them naturally to connect thoughts or set up payoffs.

### Specificity & Honesty
- **Be concrete:** "Paste your treasury address to see you run out of USDC in 47 days" beats "powerful analytics capabilities".
- **Show, don't describe:** "Three clicks from wallet connect to risk score" beats "seamless UX".
- **Include friction:** Mention actual obstacles, bugs, or trade-offs.
- **Use contractions:** "don't", "can't", "it's" (unless formal contract/legal).
- **Never invent data, studies, or quotes:** If uncertain, use "roughly", "around", or state the boundary. Never invent fake precision.
- **No marketing tails:** Cut consequence-selling tails (", ensuring X", ", so you never have to worry about Y").

### Context-Specific Rules (Chat, Email, PR, Social)
- **No restating questions:** Never open with "So you're asking about X...". Answer immediately.
- **No CTA closers:** Cut "Let me know if you have questions", "Feel free to reach out", "Happy to dig deeper".
- **No markdown in plain text:** No raw asterisks in SMS, email, or DMs.
- **No emoji as bullet lists:** No lines prefixed with ✅ or 🔥.

### Pre-Output Self-Check
1. Banned words/phrases present? → Replace with concrete terms.
2. Three consecutive same-length sentences? → Vary length.
3. Parataxis (3+ short declaratives in a row)? → Connect with conjunctions/clauses.
4. Tripled list? → Break pattern.
5. Hedging instead of committing? → State stance.
6. More than one em dash? → Cut.
7. Passive voice? → Make active.
8. Unnecessary summary at end of paragraphs? → Drop.
9. Fake data/quotes/statistics? → Replace or qualify.
10. Restated user's question or ended with boilerplate CTA? → Strip.
11. Any sentence without a main verb, or ending on a bare auxiliary? → Complete it or cut it.
12. Register check: does this read as typed in the venue it lands in (reply box, email, doc), or as an essay pasted into it? → Rewrite at the venue's register (see Contextual Sloppiness).
13. Sentence-structure check: any sentence that defines its subject ("X is the part that..."), mirrors its pair clause for clause, or lets an abstraction perform a tidy reporting verb ("status shows", "treats it that way")? → Restate it as an event with a concrete subject (see Sentence-Structure Slop).
14. Beat and voice check: does any paragraph end on a short placed beat, and does the person stay the same from the first sentence to the last? → Fold beats into the flow; hold one voice throughout.

---

## Phase 2: Measurement & Voice Profiling

Prose over 300 words can be statistically verified using the scripts in `scripts/`:

### Measurement Commands
```bash
python scripts/detect_slop.py <file>            # Standard report
python scripts/detect_slop.py <file> --verbose  # Show all hits and line numbers
python scripts/detect_slop.py <file> --json     # Machine-readable JSON output
python scripts/detect_slop.py --selftest        # Verify detector calibration
```

### Score Bands
- **< 20:** Clean, human-sounding prose.
- **20 - 40:** Marginal; minor AI patterns worth a quick cleanup pass.
- **40 - 60:** Heavy AI signals; needs structural and vocabulary revision.
- **> 60:** Generic machine slop; rewrite from scratch.

*Note:* Rhythm analysis runs on prose (`.md`, `.txt`, `.rst`, extensionless). Code files (`.cs`, `.ts`, `.py`) run phrase checks only.

### Learn a Voice Profile
Calibrate detection against the author's real writing:
```bash
python scripts/detect_slop.py --learn sample1.md sample2.md sample3.md
```
Writes `~/.claude/voice-profile.json` with author-specific medians (burstiness, sentence length, contraction rate, passive rate, vocabulary breadth). Subsequent runs evaluate against these actual targets instead of generic heuristics.

To extract clean writing samples from Claude chat history:
```bash
python scripts/harvest_prompts.py     # Writes extracted text to ~/.claude/voice-corpus/
```

---

## Phase 3: Automated & Manual Cleanup

### Automated Script Cleanup
```bash
python scripts/clean_slop.py <file>              # Preview substitutions
python scripts/clean_slop.py <file> --save       # Apply fixes (creates .backup file)
python scripts/clean_slop.py <file> --aggressive # Deep substitutions (review diff carefully)
```
Automated cleanup handles mechanical issues (banned phrases, filler, wordy transitions, buzzwords). Structural issues (sentence uniformity, parataxis, lack of depth) require manual author editing.

---

## Phase 4: Code, Design, and Second-Order Slop

Consult the reference guides in `references/`:
- [references/banned-words.md](references/banned-words.md): Banned vocabulary, phrases, openers, and model-specific tells.
- [references/sentence-patterns.md](references/sentence-patterns.md): Positive sentence patterns from Dickens and Austen (fact-first openings, colon frames, claim;evidence, long-then-short rhythm) with transfer rules for short professional writing.
- [references/text-patterns.md](references/text-patterns.md): Full catalogue of overused transitions, filler, and corporate jargon.
- [references/code-patterns.md](references/code-patterns.md): Programming antipatterns (generic names like `data`/`result`/`temp`, comments restating code, speculative abstraction, single-implementation interfaces).
- [references/design-patterns.md](references/design-patterns.md): Visual/UI antipatterns (purple-cyan gradients, card spam, uniform weight, generic hero copy).

### The Second-Order Register ("Clever Slop")
Text written under anti-slop rules often drifts into hyper-stylized writerly idiom:
- Personified artifacts ("the table went", "the architecture wanted").
- Transaction metaphors ("buys a second code path").
- Posture verbs ("sits close enough" instead of "is").
- Smug compression ("which only bites when you scan").

**The Standup Test:** Would an experienced engineer say this aloud in standup without feeling self-conscious or performative? If not, use plain factual verbs.

### Contextual Sloppiness
Slop is judged against where the text lands, not only against the text. A passage can be phrase-clean, well within every metric, and still read as machine-written in context:
- **Register mismatch:** A forum reply composed like an essay — claim, colon, evidence, conclusion, every sentence landing cleanly in sequence — reads as generated in a reply box, however clean its phrases are. Match the venue's grain: comments are ragged, mail is plain, docs are structured.
- **Composed cadence:** Uniformly finished sentences are the tell. Real writing in casual venues has uneven weight: a half-thought, an aside, a point made once and left alone.
- **Do not fake the fix:** Manufactured roughness (stock idioms, deliberate typos, slang the author never uses) is second-order slop with extra steps. Write less composed instead: fewer balanced constructions, no aphorism openers, let one sentence carry two thoughts.

**The Reply-Box Test:** Would this look typed into this exact box by the person whose name is on it? If it reads like an article excerpt pasted into a comment, rewrite it at the venue's register before posting.

### Sentence-Structure Slop ("Grammatical Slop")

A sentence can be complete, correct and still slop. Grammar is not the tell; construction is. Composed prose builds balanced, periodic sentences that arrive fully packaged. Typed prose is loose: the main clause lands first and the facts trail after it, joined by commas, "and" and "because", at uneven lengths. Three shapes give composed construction away:

- **Definition frames:** "The daemon is the part that stays up." The sentence defines its subject instead of reporting an event. State the event instead: "The daemon keeps running."
- **Balanced mirror pairs:** "The daemon stays up; the extension connects to it." Two clauses of near-equal weight facing each other across a semicolon or comma. Real replies do not come in matched pairs; break the symmetry and let the sentences differ in length and weight.
- **Abstract subjects with tidy reporting verbs:** "Status shows it as not connected." "The daemon side already treats it that way." A system, a "side", a state performs a summarizing verb on an abstraction, and no concrete fact survives. Name the actor a person would name and the words they would actually see: "You run agent-bridge status and it tells you the extension is disconnected."

The fix is structural, not lexical: concrete subjects (I, you, the call, the daemon), verbs that name physical events (fails, drops, keeps running) over verbs that summarize (treats, handles, shows), and loose sentences over periodic ones. The detector flags definition frames and vague handling verbs mechanically; mirror pairs and abstract subjects are judgment calls, caught by self-check item 13.

Two more composed habits ride along with these (both called out by San, 2026-10-26, across five drafts of one Reddit reply):

- **Paragraph-end beats:** a short, finished sentence parked at the end of a longer paragraph to land a point — "The daemon keeps running." People typing do not place beats; the weight sits wherever the thought ended. If a paragraph ends on a sentence much shorter than the ones before it, fold the fact into the flow or move it mid-paragraph. The detector flags this shape when the final sentence is a fraction of the paragraph's average.
- **Voice flipping:** impersonal system-talk for two paragraphs, then a sudden "I" in the third. Assembled text switches person because it was written in sections. A reply has one speaker: pick the person (usually "I" for an author answering about their own work) and hold it from the first sentence.

Uniform finish is the background condition for both: when every sentence is medium-length and lands cleanly, the paragraph reads edited rather than typed, whatever its phrases score. Let lengths scatter — one long loose sentence can carry a paragraph that also holds a four-word one, as long as the short one is not parked at the end as a beat.

---

## Automated Hooks Integration

- `~/.claude/hooks/voice-guard.py`: UserPromptSubmit hook; intercepts writing-related prompts and injects the generation rules and profile constraints.
- `~/.claude/hooks/slop-check.py`: Post-tool-use hook; checks edited files with `detect_slop.py --json` and emits a warning if the slop score exceeds 20.