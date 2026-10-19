---
name: grounded-planning
description: Use when writing or reviewing an implementation plan, technical spec, or design choice for an existing codebase, or when comparing two competing plans. Anchors the plan in the as-built code, real measurements and real environment facts, and rejects textbook over-engineering.
---

# Grounded Planning (`grounded-planning`)

## Overview
A grounded plan is built from what the code, logs, and tickets actually say. It doesn't come from what the prompt claims, what a textbook architecture looks like, or what a number "probably" is. Read the files first, then choose the smallest design that solves the measured problem.

**Output contract.** A plan has these sections in this order: as-built trace with file:line; options as requested with a fixed-dimension table; chosen design; protocol/IPC; lifecycle rules; files touched (existing before new); roadmap with one commit per step and an observable done-condition each; test matrix with fault injection; out of scope; decisions left to the user.

## The Textbook Architect Trap
Asked to act as a senior architect, an agent reaches for long-running pools, custom wire formats, cross-job reuse for theoretical throughput, new interfaces, heartbeats, and compatibility layers. The result looks impressive, but it doesn't match how the code runs. Every mechanism in a plan has to earn its place against the code that exists today.

---

## The 4 Grounding Checks (Step 0)

Run these against the real codebase before proposing a design.

| # | Check | Question |
|---|---|---|
| 1 | Lifespan | Does the host process live as a daemon or as a short-lived companion, and what's its own shutdown timer? |
| 2 | Plumbing | Which channels already connect the processes (stdio, pipes, sockets, files)? |
| 3 | Isolation | Does reusing state across jobs risk leaks, hangs, or dirty-state contamination? |
| 4 | Boundaries | Who owns the target files, which open PRs touch them, and how large is the reviewable diff? |

### 1. Runtime Lifespan
Find when and why the host starts and stops, and read the host's idle or shutdown timer in code. A worker, cache, or idle policy must fit inside that lifetime, because a plan that keeps workers alive for minutes inside a host that exits seconds after its last session leaves orphans or never runs at all.

### 2. Existing Plumbing
List the channels that already connect the processes and use them first. An anonymous parent-child pipe doesn't need access control, has no name to collide on, and reports peer death through EOF. A new socket, named pipe, or file drop needs an explicit reason why the existing channel can't carry the data.

### 3. Failure Domain and Blast Radius
Ask what a crash or a dirty input does to the next job. Prefer a fresh process per job unless a measured bottleneck says otherwise, since a pre-warmed standby gives low start latency without sharing state between jobs.

### 4. Ownership, Open PRs, and Diff Budget
List the open PRs and branches that touch each target file, and name the one the plan builds on. A plan written against `main` while an open PR already rewrote the target function is a stale-base plan. Keep the diff to as few existing files as the problem allows so the owner can review it quickly.

---

## Grounded vs. Textbook (generic)

| Dimension | Textbook | Grounded |
|---|---|---|
| Process model | Persistent multi-slot pool with scaling | One job per child, at most one warm standby |
| Transport | New socket or named pipe with custom framing | Existing parent-child stdio, line-delimited when the payload is small |
| Death detection | Heartbeat or watchdog | Process exit, EOF, or an OS kill-on-close primitive |
| State handling | Reuse native resources across requests | Fresh resource per job, OS teardown on exit |
| Compatibility | Keep the old mode "just in case" | Keep a path only if a named caller uses it |
| Diff footprint | New classes, interfaces, and options | Split or extend the existing method |

---

## 5-Step Planning Protocol

### Step 1: Trace the as-built chain line by line
Open the source and follow the path from entry to exit, recording file:line for each step and for each cost that could move. Quote environment facts directly from the files: `TargetFramework`, package versions, settings, and timeouts. Never copy them from the prompt, so if the csproj says `net10.0-windows`, the plan says `net10.0-windows`.

### Step 2: Evaluate the options as the requester defined them
Put the requested options into one table on fixed dimensions (see "Comparing two plans"). If you rename, merge, or reshape an option, say so in one sentence and say why, but don't rewrite a requested option into a worse design just so your own choice reads as the middle ground.

### Step 3: Choose the minimal mechanism
Pick the smallest protocol and lifecycle that works. For each new mechanism (interface, heartbeat, counter, timeout, retry, or config knob), write one line naming the failure it handles that the OS or existing code doesn't already handle. If you can't write that line, delete the mechanism.

### Step 4: Check boundaries and base
List open PRs and branches per target file, name the base the plan builds on, and note who owns each file. Re-check this right before delivering the plan, because bases move during active development.

### Step 5: Build the test and fault matrix
Every row names an action and an observable result: a log line, a process list, a file on disk, or an exit code. Include fault injection: kill the child mid-job, kill the host abruptly, feed a hostile or dirty input, or hit the timeout. Cover the cold baseline, sequential multi-job throughput, and cleanup of leftover processes or handles.

---

## Evidence Rules

**Numbers.** Every number in a plan is either quoted from a named source (file, log, or ticket, with the path or id) or marked "to be measured in step N". A latency table or a pass threshold such as "< 1.0 s" that nobody measured is invented. Pass criteria are observable events, not guessed durations.

**Technical premises.** Every "X is unsafe, so we need Y" claim names the mechanism and is checked against process and thread boundaries. For instance, claiming that third-party add-ins can corrupt the worker's stdout is false when the add-ins run in a different process than the worker. If the mechanism doesn't cross the boundary, the justification and the design built on it go.

**Snippets.** Any code snippet names the real signature it calls (file:line) or is labelled pseudocode. A snippet that passes a string where the real exception constructor takes an int won't compile and shows the author never opened the type.

**Compatibility paths.** Don't keep a compatibility path without a named caller, because a legacy mode nobody calls doubles the test surface and the review burden.

**New mechanisms.** Avoid interfaces with a single implementation, heartbeats where process exit already signals death, or recycle counters whose only job is to manage a leak the design itself introduced.

---

## Comparing two plans

1. Read the other plan's actual file, not a pasted summary or a recap, because summaries drop the details that decide the comparison.
2. Check its claims with the Evidence Rules above: numbers, environment facts, premises, snippets, and base.
3. Produce a pros/cons table on fixed dimensions:

| Dimension | Plan A | Plan B |
|---|---|---|
| Grounding (cites file:line, real versions) | | |
| Isolation (state shared between jobs) | | |
| Blast radius (what one crash takes down) | | |
| IPC size (new channels, message types) | | |
| New files / existing files touched | | |
| Config knobs | | |
| Host lifetime fit | | |
| Compilability of snippets | | |
| Upgrade path | | |

4. List explicitly what you ADOPT from the rejected plan, because a rejected plan usually contains one or two correct ideas (such as carrying the child's resource pid in the ready message so the parent can verify containment with `IsProcessInJob`).
5. State what you reject along with the one-line reason for each item.

---

## Red Flags: STOP and Reset

- [ ] Adding a new socket, named pipe, or file channel while parent-child stdio already connects the processes.
- [ ] Designing a long-lived pool or an idle hold longer than the host's own shutdown timer.
- [ ] Reusing stateful native objects across requests without proof that isolation survives dirty input.
- [ ] Introducing more than two new abstractions for something that's solvable by splitting an existing class.
- [ ] Failing to read the exact lines of the current implementation and the open PRs before proposing.
- [ ] Presenting a benchmark table or pass threshold without a named source or a "to be measured" marker.
- [ ] Targeting `main` while an open PR has already rewritten the same function.
- [ ] Adopting a framework, version, or setting from the prompt instead of checking the project file.
- [ ] Justifying a design with a hazard that doesn't cross a real process or thread boundary.
- [ ] Reshaping or renaming one of the requested options without stating that you did so.
- [ ] Writing a code snippet without a signature reference and without marking it as pseudocode.
- [ ] Retaining a compatibility or legacy path that doesn't have a named caller.
- [ ] Creating an interface that only has one implementation, a heartbeat that duplicates process exit, or a counter managing a self-introduced leak.
- [ ] Picking an idle or lifetime number that ignores the host's shutdown timer.

---

## Example (one worked case)

Context: a client-side converter host drives an Office COM automation worker per document. The host exits 5 s after its last session. Conversion was slow because Office start-up happened on every job.

- As-built trace: host calls the converter, which launches the worker, starts Office, converts, and quits. Start-up is the fixed cost; the document path is the only per-job input.
- Plumbing: parent and child already share stdio. The worker prints `READY` when Office is up, then reads `<in>\t<out>` lines from stdin. EOF on stdin means the parent died.
- Isolation: one document per worker. A single warm standby starts when the first authenticated session opens, and a replacement starts as soon as the standby is claimed, so warm-up overlaps with conversion.
- Containment: a Windows Job Object with kill-on-close covers host death. The ready message carries the Office process pid so the parent can verify membership with `IsProcessInJob`.
- Lifetime: the standby has its own idle timer while sessions are open, and dies with the host when the host's 5 s idle exit fires. No hold outlives the host.
- Rejected: a named-pipe worker pool with heartbeats (new transport, new ACL surface, a watchdog for a death that EOF already reports) and a "legacy CLI mode" with no caller.
- Test matrix rows: cold single file (log shows worker start, `READY`, exit), three files in sequence (process list shows one worker at a time), kill the worker mid-job (parent reports failure, no orphan), and kill the host (Job Object removes Office within the observed teardown, checked in the process list).
