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

## Round 3: Doyle and Shakespeare

Added after close reading of Doyle (*A Study in Scarlet*, opening) and
Shakespeare (*Hamlet*, opening scenes). The Doyle excerpt ends before
Holmes reasons, so the explanation patterns are Watson's; the
Shakespeare patterns come from dialogue.

### 13. Carry-over opener (Doyle)
Each sentence opens with a short phrase that repeats where the last one
ended, then adds one new fact.
- "Having completed my studies there, I was duly attached to the Fifth Northumberland Fusiliers as Assistant Surgeon."
Use for: incident timelines and onboarding docs. Order stays clear
without a timestamp on every line.

### 14. Progress, then interruption (Doyle)
"had already [reached some level] ... when [setback]." The recovery level
comes first, so the reader can judge the second failure's impact.
Use for: incident reports with a second failure.

### 15. Averted outcome, then credit (Doyle)
Name the bad outcome first, then "had it not been for" and the person or
mechanism that prevented it.
- "I should have fallen into the hands of the murderous Ghazis had it not been for the devotion"
Use for: postmortems. Naming the prevented outcome shows the save's worth.

### 16. Confidence tag on each item (Doyle)
In a list of facts about one subject, each item carries its own source
marker: "I believe", "as far as I know", or nothing when certain.
- "I believe he is well up in anatomy, and he is a first-class chemist"
Use for: status lists. "Confirmed: the cert expired. Likely: renewal
failed on the cron host. Unknown: why the alert stayed silent."

### 17. Dash correction to a measured limit (Doyle)
A broad claim, a dash, then the same claim narrowed to a hard number.
The writer corrects their own claim on the page.
- "as free as air—or as free as an income of eleven shillings and sixpence a day will permit"
Use for: status updates that would otherwise overclaim. "Migration is
done—or done for the 94% of tenants already on v3." One em dash per piece
at most (see the punctuation rules).

### 18. Concrete null report (Shakespeare)
A status question gets a negative answer phrased as the smallest thing
that would have shown up.
- "Have you had quiet guard?" / "Not a mouse stirring."
Use for: on-call handoffs. "No pages, no retries, queue depth flat."

### 19. Symptom-question stack, answer mapped back (Shakespeare)
Parallel "why" questions, one per observation, then one closing question
asking for the shared cause. The reply names the cause once and points it
at each symptom, in the asker's terms.
Use for: escalation mails and RCA summaries.

### 20. The skeptic's prior, then what changed it (Shakespeare)
State the belief held before, then the evidence that replaced it.
- "I might not this believe / Without the sensible and true avouch / Of mine own eyes."
Use for: motivation sections. "I assumed this was a flaky test until I
reproduced it on a clean VM."

### Antithesis: the ban stands
Shakespeare's antithesis pairs two things that are both true ("make the
night joint-labourer with the day"). "Not X, but Y" invents a wrong view
so it can correct it, and that invented opponent is the tell. Reading
Shakespeare confirms the banned-words rule; it does not relax it.

### Added transfer rules

14. Open each timeline sentence with a short phrase that repeats where
    the last one ended.
15. Tag confidence or source on each item in a status list, never once
    for the whole list.
16. When crediting a save, name the outcome it prevented first.
17. Report a null as the smallest thing that would have shown up.
18. When answering several questions, end by pointing the cause at each
    question in the asker's terms.

## Round 4: Strunk, The Elements of Style (1918)

Not fiction: a style manual, read against the existing rules. Most of
Strunk is already covered (fact-first, active voice, concrete language,
claim;evidence, parallel form). What follows is only what he adds, plus
the conflicts and how they resolve.

### 21. One topic per paragraph, end on the consequence
A paragraph opens on its claim and closes on the consequence, never on a
digression or an unimportant detail.
Use for: docs, mail, PR descriptions. "So the cache must be per-tenant."

### 22. Give the action back to the verb
When a noun names the whole action and the verb only completes the
sentence, turn the noun into the verb. "A review of the logs was
conducted" becomes "We reviewed the logs." Watch for "there is" forms,
which are technically active and still dead.

### 23. Say what is
"Not" is for denial or antithesis, never evasion. Replace the negated
phrase with its positive word or a number: "did not remember" becomes
"forgot"; "coverage is not great" becomes "two of the five handlers have
tests".

### 24. Put the new element last
The end of a sentence is the emphatic position; it should hold the new
information. Context goes first. "We rolled back because of the memory
leak" becomes "Because of the memory leak, we rolled back" when the
rollback is the news. Fact-first orders sentences; this orders words
inside one.

### 25. Keep related words together
Subject next to its verb; a relative pronoun right after its word;
"only" and "not all" next to the word they limit. "All the tests did not
pass" becomes "Not all the tests passed."

### 26. Vary clause structure, not only length
A run of two-clause sentences joined by and/but/so/which/while drones,
even when the lengths vary. Recast some as simple sentences, semicolon
pairs, or periodic sentences, whichever matches the real relation.

### 27. Same thing, same word
Ideas of equal rank take the same form and the same name. Rotating
synonyms for variety makes readers hunt for a difference that is not
there, and reads as machine writing. Past about seven parallel items,
use a table.

### 28. Summaries: one tense, one attribution
Keep one tense through a summary. Attribute once at the top, then stop
writing "he added". In a review, lead with the conclusion and use the
source's details as evidence.

### 29. "Fact" is for the verifiable
Call something a fact only when it can be directly verified, not when it
is a judgment. Judgments take a confidence tag (pattern 16): "I think
Postgres fits better." Facts: "the cert expired at 03:00 UTC."

### Conflicts, resolved
- Short sentences vs combining: merge three or more short sentences that
  are steps in one causal chain (the full stops hide the "because").
  Keep the short sentence when it follows a long one and states the
  verdict or result. Test: if two sentences join with "so" or "because"
  and nothing is lost, merge them.
- One-sentence paragraphs: at most two per post (the hook, one turn).
  Every line as its own paragraph is itself a tell. In docs and mail,
  one topic per paragraph with at least two sentences.
- "Not X, but Y": allowed only when X is a claim the reader has actually
  heard and the source is named. Otherwise the ban stands.
- Qualifier-last vs end-weight: a one- or two-word qualifier may end the
  sentence ("It's done, mostly"). A whole qualifier clause moves to the
  front, so the sentence ends on the claim.
- "So" turns: at most one per paragraph, as its own sentence after a
  setup. Never two "X, so Y" compounds in a row.
- Strunk's dated rules lose to modern usage: singular "they" is fine;
  shall/will by person, the split-infinitive ban and "to-day" are period
  style, not rules.

### Added transfer rules

19. Put the new or decisive information at the end of the sentence, the
    context at the front.
20. When a noun names the action, turn it into the verb.
21. When "not" softens a judgment, replace it with the positive word or
    a number.
22. Call one thing by one name throughout; never rotate synonyms.
23. One topic per paragraph: open on the claim, close on the consequence.
