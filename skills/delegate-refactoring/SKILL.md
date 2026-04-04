---
name: delegate-refactoring
description: >-
  Entry point for issue-driven autonomous refactoring. Accepts a GitHub
  issue URL or number, validates it, and orchestrates the full workflow:
  worktree creation, code changes, PULL-REQUEST.md preparation, privacy
  scan, human review gate, and publishing. Use when asked to work on an
  issue autonomously, refactor across repos, or delegate coding work to
  the refactoring agent.
allowed-tools: Bash(gh*) Read Agent
---

# Delegate Refactoring

Orchestrate the full issue-to-PR workflow. This skill is the entry point
— it sets up the work and enforces the process.

## Step 1: Validate the issue

Accept a GitHub issue URL or `owner/repo#number`. Read the issue:

```bash
gh issue view <number> --repo <owner/repo> --json title,body,labels,state
```

Check:
- Issue is OPEN
- Body has enough detail to act on (not just a title)
- If insufficient, ask the human what the issue needs before proceeding

## Step 2: Determine the target repo

From the issue URL, identify which repo the work targets. Verify it's
cloned locally. If not cloned, ask the human whether to clone it.

## Step 3: Check repo visibility

```bash
gh repo view <owner/repo> --json visibility -q '.visibility'
```

If PUBLIC: all safety gates are mandatory. No autonomous GitHub writes.
If PRIVATE: safety gates still apply but human may choose to relax them.

## Step 4: Create worktree

The agent works in an isolated worktree. The main checkout is never
touched.

```bash
git worktree add /tmp/claude-agent/<repo>-<issue>-$$ agent/issue-<number>
```

All subsequent work happens in the worktree directory.

## Step 5: Do the work

This is where the agent reads the issue, plans changes, writes code,
and runs tests. The agent should:

- Commit freely to the feature branch (local only, messy is fine)
- Invoke skills as needed:
  - `sociable-unit-tests` when writing tests
  - `identify-best-practices` for design decisions
  - `setup-agent-context` when touching repo config
  - `code-reuse` when patterns should be shared
  - `author-github-issue` if sub-issues need to be filed

## Step 6: Write PULL-REQUEST.md

Commit a `PULL-REQUEST.md` to the feature branch:

```yaml
---
title: Short PR title (under 70 chars)
closes: <issue-number>
---

## Summary
- What changed and why (1-3 bullets)

## Test plan
- How to verify the changes work
```

This file travels with the branch. It will be consumed by
`publish-pull-request` and will NOT reach main (squash-merge drops it).

## Step 7: Run privacy scan

Invoke the `privacy-scan` skill. It checks:
- Squashed diff
- All commit messages on the branch
- PULL-REQUEST.md title and body
- Branch name

If findings: fix them, re-run the scan. Repeat until clean.

## Step 8: HARD STOP — present to human

**You MUST stop here and present the following to the human:**

1. Code diff: `git diff main..agent/issue-<number>`
2. PULL-REQUEST.md content
3. Privacy scan results (should be clean)

**Do NOT proceed without explicit human approval.** Wait for the human
to say "go", "LGTM", "ship it", or equivalent.

If the human requests changes, go back to Step 5.

## Step 9: Publish

Delegate to `publish-pull-request` skill. That skill handles:
- Squash-merge to main
- Push
- PR creation via `gh pr create`

## Step 10: Clean up

```bash
git worktree remove /tmp/claude-agent/<repo>-<issue>-$$
git worktree prune
```

The feature branch can be deleted after the PR merges.

## Recovery

If the agent crashes or the session is interrupted:

- The branch still exists in the repo's `.git/` — commits are safe
- The worktree may be stale: `git worktree prune` cleans it up
- Resume by creating a new worktree from the existing branch
- Continue from wherever the work left off

## What this skill does NOT do

- Push to public repos autonomously
- Create PRs without human approval
- Bypass the privacy scan
- Work without a GitHub issue (the issue is the contract)
