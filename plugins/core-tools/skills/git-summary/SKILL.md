---
name: git-summary
description: Generate concise, caveman-style git activity summary across recent commits, branches, and staged diffs.
platforms: [linux, macos, windows]
---

# Git Summary Skill

Generates concise, token-efficient summary of git repository activity.

## When to Use
- User asks for repo status, git overview, recent branch work, or staged change breakdown.
- User invokes `/git-summary` or `git-summary`.

## Instructions
1. Run `git status -s` to inspect working tree state.
2. Run `git branch --show-current` to get active branch name.
3. Run `git log -n 5 --oneline` for last 5 commits.
4. Output ultra-terse summary:
   - Branch name
   - Staged / modified / untracked file count
   - Recent commit hashes and subjects
   - Key blockers or unstaged risks
