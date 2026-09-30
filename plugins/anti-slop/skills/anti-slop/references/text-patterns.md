---
name: text-patterns
description: Reference guide for detecting AI slop patterns in natural language text including overused phrases, buzzwords, and meta-commentary. Use as reference when reviewing text content for quality.
---

# Text Slop Patterns

This reference documents common "AI slop" patterns in natural language writing that should be avoided or cleaned up.

## Table of Contents
- Overused Transition Phrases
- Generic Hedge Language
- Unnecessary Meta-Commentary
- Corporate Buzzword Clusters
- Redundant Qualifiers
- Empty Intensifiers
- Filler Constructions
- Writerly Idiom Register (Second-Order Slop)
- Detection Patterns

## Overused Transition Phrases

These phrases appear disproportionately in AI-generated text and signal low-quality content:

### High-Risk Phrases (Nearly Always Slop)
- "delve into"
- "dive deep into"
- "unpack"
- "navigate the complexities"
- "in the ever-evolving landscape"
- "in today's fast-paced world"
- "in today's digital age"
- "at the end of the day"
- "it's important to note that"
- "it's worth noting that"
- "in conclusion" (in contexts where it's obvious)

### Medium-Risk Phrases (Often Slop in Certain Contexts)
- "however, it is important to"
- "furthermore"
- "moreover"
- "in essence"
- "essentially"
- "fundamentally"
- "ultimately"
- "that being said"

## Generic Hedge Language

Excessive hedging that adds no value:

- "may or may not"
- "could potentially"
- "might possibly"
- "it appears that"
- "it seems that"
- "one could argue"
- "some might say"
- "to a certain extent"
- "in some cases"
- "generally speaking"

**Better approach:** Be direct. If uncertain, state the uncertainty concretely.

## Unnecessary Meta-Commentary

Self-referential statements that add no information:

- "In this article, I will discuss..."
- "As we explore..."
- "Let's take a closer look..."
- "Now that we've covered..."
- "Before we proceed..."
- "It's crucial to understand..."
- "We must consider..."

**Better approach:** Just say the thing. Skip the stage directions.

## Corporate Buzzword Clusters

Excessive business jargon that obscures meaning:

### Meaningless Modifiers
- "synergistic"
- "holistic approach"
- "paradigm shift"
- "game-changer"
- "revolutionary"
- "cutting-edge" (when not literally about edges)
- "next-generation"
- "world-class"
- "best-in-class"
- "leverage" (when "use" would work)
- "utilize" (when "use" would work)

### Vague Action Phrases
- "drive innovation"
- "unlock potential"
- "empower users"
- "enable success"
- "foster growth"
- "facilitate collaboration"
- "optimize outcomes"
- "maximize value"

## Redundant Qualifiers

Phrases that repeat themselves:

- "completely finish"
- "absolutely essential"
- "totally unique"
- "very unique"
- "really important"
- "quite significant"
- "past history"
- "future plans"
- "end result"
- "final outcome"

## Empty Intensifiers

Words that try to add emphasis but fail:

- Overuse of "very"
- Overuse of "really"
- Overuse of "extremely"
- Overuse of "incredibly"
- "quite literally"
- "actually" (when not contrasting)

## Filler Constructions

### Wordy Phrases with Simple Alternatives
| Wordy | Simple |
|-------|--------|
| "in order to" | "to" |
| "due to the fact that" | "because" |
| "at this point in time" | "now" |
| "for the purpose of" | "for" |
| "has the ability to" | "can" |
| "is able to" | "can" |
| "in spite of the fact that" | "although" |
| "take into consideration" | "consider" |
| "make a decision" | "decide" |
| "conduct an investigation" | "investigate" |

### Existential Constructions
- "There are many people who..." → "Many people..."
- "It is important to..." → Just state the important thing
- "There exists a need for..." → "We need..."

## Writerly Idiom Register (Second-Order Slop)

Shows up when generation was explicitly told to avoid the patterns above. The model swaps
corporate filler for creative-writing punch, and the result is a register no engineer uses:
clever compression where a plain verb was available. Phrase-list detectors and the rhythm
metrics both score it clean, because the vocabulary is clean and the sentences vary. Only a
read catches it.

### Personified artifacts

Tables, constants, and designs doing human things:

| Slop | Plain |
|------|-------|
| "the table went" | "I dropped the table" |
| "the first design wanted four tables" | "the first design had four tables" |
| "the constant reads 80" | "the constant is 80" |
| "a guess sitting in production" | "a guess in production" |

### Transaction metaphors for tradeoffs

| Slop | Plain |
|------|-------|
| "it buys a second code path" | "it adds a second code path" |
| "calls went in the bin" | "calls were wasted" |
| "the only thing renewal buys" | "the only gain from renewal" |

One in a document is how people talk. Recurring, it's a register.

### Posture and motion verbs where "is" works

| Slop | Plain |
|------|-------|
| "0.90 sits close enough to live traffic" | "0.90 is close enough to live traffic" |
| "sits one step past the measurement" | "is one step past the measurement" |
| "takes a different route" | "follows a different path" |
| "pull that under a minute" | "bring that under a minute" |

### Cute compression

- "which only bites when you scan" → "which only matters when you scan"
- "quietly becoming 'and also not a sibling thread'" → state the caveat plainly
- Two-word punch fragments after a setup sentence: "Both shipped."

### The standup test

Would an engineer say the phrase aloud in a standup without noticing they'd been clever?
"Runs on a 32GB box" passes. "The table went" fails.

### What to keep

Genuine dev vernacular is not this pattern, and flattening it is the humanizer trap in
reverse: "box" for machine, "wedged" for hung, the "knee" of a curve, "fenced on
worker_id", a "trap" in an API, "kill a process", "ties up workers". Strip those and the
text stops sounding like an engineer at all.

Density is the signal. Any one phrase alone is fine. A document where every third sentence
has one was written by a model told to sound human.

## Detection Patterns

### Sentence-Level Red Flags
1. Sentences starting with "It is important to note that"
2. Sentences with 3+ hedge words ("might possibly perhaps")
3. Sentences with both "navigate" and "landscape/complexity"
4. Opening sentences that describe what the text will do instead of doing it

### Paragraph-Level Red Flags
1. Opening paragraphs that are pure meta-commentary
2. Paragraphs that restate the title in different words
3. Closing paragraphs that say "in conclusion" then summarize without adding insight
4. Every paragraph starting with a transition word

### Document-Level Red Flags
1. High density of buzzwords (>5% of unique words)
2. Excessive passive voice (>30% of sentences)
3. High Flesch-Kincaid grade level without justification
4. Generic structure: intro meta-commentary, list of points, conclusion meta-commentary

## Cleanup Strategies

### Immediate Cuts
Remove entirely:
- Meta-commentary about what you will discuss
- Obvious transitions between clearly connected ideas
- Redundant qualifiers
- Empty intensifiers

### Rewrites
- Turn passive voice to active
- Replace buzzwords with specific terms
- Replace hedge clusters with one precise statement
- Replace wordy constructions with simple alternatives

### Structural Improvements
- Lead with the actual point, not a preamble
- Use concrete examples instead of abstract statements
- Break up walls of uniform paragraph structure
- Vary sentence length and structure

## Context Matters

Not all these patterns are always slop. Consider:

- **Audience**: Academic writing may need more hedging than blog posts
- **Purpose**: Legal documents need precision; marketing needs energy
- **Length**: Longer pieces need more transitions than short ones
- **Domain**: Technical writing has different norms than creative writing

The key is *overuse* and *unconscious repetition*, not the existence of these patterns.
