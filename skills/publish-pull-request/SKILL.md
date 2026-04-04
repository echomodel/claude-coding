---
name: publish-pull-request
description: >-
  Mechanical skill for publishing a reviewed branch as a PR. Use ONLY after
  the human has reviewed and approved the code diff, PULL-REQUEST.md content,
  and privacy scan results. This skill squash-merges, pushes, and creates
  the PR. No judgment, no creativity — a deployment script.
allowed-tools: Read Bash(git*) Bash(gh*)
---

# Publish Pull Request

You are a deployment script. Follow these steps exactly. Do not skip steps.
Do not improvise. Do not add commentary beyond status updates.

## Prerequisites

Before this skill runs, the following MUST already be true:
- Human has reviewed the code diff
- Human has reviewed PULL-REQUEST.md (title + body)
- Privacy scan has passed
- Human has explicitly said to proceed

If any of these are uncertain, STOP and ask.

## Step 1: Read PULL-REQUEST.md from the branch

```bash
git show <branch>:PULL-REQUEST.md
```

Parse the frontmatter:
- `title:` — the PR title
- `closes:` — optional issue number to link

The body (everything after the frontmatter `---`) is the PR body.

## Step 2: Squash-merge the branch to main

```bash
git checkout main
git pull origin main
git merge --squash <branch>
```

If there are merge conflicts, STOP and report them. Do not resolve
conflicts autonomously.

## Step 3: Commit with clean message

Use the title from PULL-REQUEST.md as the commit subject. If there's a
`closes:` field, append it.

```bash
git commit -m "<title from PULL-REQUEST.md>"
```

The PULL-REQUEST.md file is NOT included in the squash-merge because it
was on the feature branch, not on main. This is correct — it was a
branch-only artifact.

## Step 4: Push

```bash
git push origin main
```

## Step 5: Create the PR

If the work was done on a branch that should be PRed (not direct to main):

```bash
git push origin <branch>
gh pr create --title "<title>" --body-file <(echo "<body from PULL-REQUEST.md>")
```

If `closes:` was specified:
```bash
gh pr create --title "<title>" --body-file <(echo "<body>") 
```

The body should include `Closes #<number>` to auto-link the issue.

## Step 6: Report

Print:
- PR URL
- Commit SHA
- Branch name
- Whether issue was linked

## What this skill does NOT do

- Review code
- Run privacy scans
- Make judgment calls about whether to proceed
- Modify any code
- Write or edit PULL-REQUEST.md
