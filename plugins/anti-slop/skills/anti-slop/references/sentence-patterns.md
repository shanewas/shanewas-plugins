# Sentence Patterns from Classic English Prose

Positive patterns, extracted from Dickens (*A Christmas Carol*) and Austen
(*Pride and Prejudice*, ch. 1) by close reading. The banned-words and
text-patterns references say what to avoid; this file says what to build
instead. All quotations are public domain.

## Patterns

### 1. Main fact first, colon attaches the frame (Dickens, Austen)
State the key fact in a short main clause. A colon then adds the list,
qualifier or counterpart it needs.
- "Marley was dead: to begin with."
- "The business of her life was to get her daughters married: its solace was visiting and news."
Use for: release notes, status lines, summaries that pair a goal with a
constraint or a cause with its effect.

### 2. Long sentence, then a short flat one (Austen, Dickens)
Let a long, clause-carrying sentence do the explaining. Follow it with a
sentence of four to eight words that settles the matter.
- "Mr. Bennet made no answer."
Use for: the outcome or decision after a complicated explanation. Never
write three long sentences in a row.

### 3. Claim; evidence (Austen)
A general statement, a semicolon, then the specific detail that proves it.
- "'Kitty has no discretion in her coughs,' said her father; 'she times them ill.'"
Use for: bug reports, reviews, incident notes. "The cache is unreliable;
it serves stale entries after a deploy."

### 4. Semicolon action chain (Dickens)
Independent clauses that share one subject, joined by semicolons, one verb
and its object each. No "and then."
- "He carried his own low temperature always about with him; he iced his office in the dog-days"
Use for: sequences of related actions or symptoms in one breath.

### 5. Concession, then limit (Austen, Dickens)
Admit the point first, then "but" and the limit. The claim lands at the end.
- "I certainly have had my share of beauty, but I do not pretend to be anything extraordinary now."
Use for: trade-off statements in reviews and recommendation mails.

### 6. Mid-sentence concessive
Subject, a comma-fenced "though..." phrase, then the predicate. The main
clause wraps around the qualifier, so no second sentence is needed.
- "The plot, though not elaborate, is almost regular enough for Fielding" (Saintsbury, on Austen)
Use for: "The fix, though small, ended the outages."

### 7. Bare claim, then shut the door (Dickens)
A short declarative followed by an even shorter one that rules out doubt.
No subordination at all.
- "There is no doubt whatever about that."
Use for: status updates and decisions, sparingly.

## Grammar habits behind the patterns

- Mostly active voice. Passive is reserved for record-like facts where
  the actor does not matter.
- Few adjectives, and most are judgments, not decoration. Cut any
  adjective that changes no fact.
- "No" + noun instead of "did not" + verb where it fits: "made no
  answer", "had no knowledge of it". Shorter, and final.
- Wide length variation: Dickens averages about 18 words a sentence and
  runs from 1 to about 65; Austen's narration runs about 18-22, dialogue
  5-15. Uniform length is the machine tell.
- Semicolons are common joints (Austen: roughly one sentence in six);
  colons are rarer and mark a pairing or an explanation.

## Transfer rules

1. Put the main fact in the first clause of the first sentence.
2. Follow a long sentence with a short one.
3. Use a colon to attach the frame a fact needs.
4. Join actions that share a subject with a semicolon, not "and then."
5. Admit the weakness first, then turn with "but" and end on the claim.
6. Tuck a short qualifier between commas after the subject.
7. Keep verbs active; passive only when the actor doesn't matter.
8. Cut any adjective that doesn't change a fact.

## Worked example

Before (flat, uniform, product-description rhythm):

> My AI agents kept failing on login pages and bot checks when they used a
> fresh browser profile. My normal Chrome was already signed in to the
> sites I needed. agent-browser-bridge connects a local Python process to
> my open Chrome and Edge tabs over a WebSocket, so agents can work in the
> browser I already use. v3.0.0 is on PyPI. The extension is on the Chrome
> Web Store and Edge Add-ons. Most of the work went into Manifest V3.

After (fact first, colon frame, long-then-short, semicolon chain):

> agent-browser-bridge v3.0.0 is on PyPI, with the extension for Chrome
> and Edge. It connects a local Python process to my open Chrome and Edge
> tabs over a WebSocket, so the agent works in the browser I already use.
>
> It fixes a problem I kept hitting: in a fresh browser profile, my AI
> agents failed on login pages and bot checks, while my normal Chrome was
> already signed in to the sites I needed.
>
> Most of the work was Manifest V3. Chrome kills the extension service
> worker after about 30 seconds idle, and the WebSocket connection dropped
> with it. I added a heartbeat; when the worker restarts, the extension
> reconnects and restores tab state.

## Round 2: Twain and Tagore

Added after close reading of Twain (*Adventures of Huckleberry Finn*,
opening) and Tagore (*Gitanjali*, opening poems). Only the patterns that
transfer to professional writing; dialect, refrain and lyric imagery were
tested and dropped.

### 8. Deadpan juxtaposition (Twain)
Two facts that contrast, set down in separate flat sentences. No comment,
no "ironically", no "while" clause smoothing the gap. The reader sees the
contrast unaided.
- "And she took snuff, too; of course that was all right, because she done it herself."
Use for: problem statements where the contradiction is the point.

### 9. "So" turn (Twain)
A few sentences of setup, then a short sentence starting with "So" carries
the result. The logic is explicit but reads as speech, not argument.
- "So I made up my mind I wouldn't try for it."
Use for: the move from problem to response in a post or report.

### 10. Qualifier last (Twain)
State the claim at full strength, then the honest limit in as few words as
possible, at the end.
- "He told the truth, mainly."
Use for: claims with one exception. The reverse of concession-first.

### 11. Verdict first, then the condition (Tagore)
Lead with the judgment, then the condition it depends on.
- "It is no gain, thy bondage of finery, if it keep one shut off from the sound health of the dust."
Use for: trade-offs. "A clean profile is no help if the site wants a login."

### 12. Parallel items, shared frame, reason attached (Tagore)
Parallel items keep one sentence frame, and each item carries its own
reason inside its own sentence.
Use for: design-decision lists and changelogs. "We pin X, because Y.
We retry Z, because W."

### Added transfer rules

9. Put contrasting facts in separate flat sentences; don't smooth them
   with "while" or flag them as ironic.
10. After a setup, start the consequence sentence with "So".
11. State the claim first and the qualifier last, in as few words as
    possible.
12. Give parallel items one shared frame, with each item's reason inside
    its own sentence.
13. For trade-offs, verdict first, then the condition it depends on.
