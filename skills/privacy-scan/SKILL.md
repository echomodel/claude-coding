---
name: privacy-scan
description: >-
  Scan staged changes, commit messages, and PR metadata for personal
  information, credentials, workspace paths, and private context before
  publishing. Use before any push, PR creation, or issue write to a
  public repo. Complements pre-publish-privacy-review with a focus on
  the specific artifacts produced by the refactoring agent workflow.
allowed-tools: Read Bash(git*) Grep
---

# Privacy Scan

Scan the agent's work output for content that must not reach public
GitHub. This is a focused, mechanical review — not a conversation.

## What to scan

### 1. Squashed diff

```bash
git diff main..<branch>
```

Check the actual code changes for:
- Hardcoded credentials, API keys, tokens, secrets
- Real email addresses, phone numbers, names
- Workspace-specific absolute paths (e.g., `/home/<username>/...`)
- GCP project IDs, Google Doc/Sheet IDs, account IDs
- Personal project references that reveal the author's identity

### 2. All commit messages on the branch

```bash
git log main..<branch> --format="%s%n%b"
```

Commit messages often leak context that code doesn't:
- "Fix auth for bob's deployment"
- "Update config for my-side-project"
- References to personal repos, usernames, or workspace layout

### 3. PULL-REQUEST.md

Read the file from the branch:

```bash
git show <branch>:PULL-REQUEST.md
```

Check both the title (frontmatter) and the body for:
- Personal context from the issue that motivated the work
- Workspace paths or personal project references
- Anything that identifies the author beyond their GitHub username

### 4. Branch name

```bash
git rev-parse --abbrev-ref HEAD
```

Branch names like `bob/fix-auth` or `my-side-project-update` leak context.

## How to report

For each finding, report:
- **Where**: which artifact (diff, commit message, PR body, branch name)
- **What**: the specific content
- **Why**: what makes it sensitive
- **Fix**: what to change it to

## If you find nothing

**That is the ideal outcome.** A clean scan is normal and expected.
Do not manufacture findings. Do not flag things that are technically
personal but obviously harmless (e.g., a commit authored by the git
user's configured name — that's how git works).

Do not re-run the scan hoping to find something. A clean scan means
proceed.

## What this skill does NOT do

- Fix findings (the agent fixes them, then re-runs the scan)
- Make judgment calls about whether to publish
- Push, commit, or create PRs
- Review code quality, correctness, or style
