---
description: Quick git repository health check and worktree status
argument-hint: [branch] (optional)
context: fork
---

# Summary Command

Run an instant snapshot of repository state:

1. Check current branch: `git branch --show-current`
2. Check uncommitted changes: `git status -s`
3. Check last 3 commits: `git log -n 3 --oneline`
4. Summarize clearly in concise bullet points.
