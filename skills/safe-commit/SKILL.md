---
name: safe-commit
description: >-
  Stage, review, scan, and commit changes safely. Use EVERY TIME the user
  says "commit", "git commit", "push", "git push", "stage and commit",
  "commit this", "commit all", "commit and push", "safe commit", "ready
  to commit", "let's commit", or any variation of committing code.
  Also use when you (the agent) decide to commit on the user's behalf
  after completing a task.
user-invocable: true
argument-hint: "[commit message]"
---

# Safe Commit

Stage, review for privacy and quality, run the privacy-guard agent,
then commit. Every commit goes through this flow — no exceptions.

## Steps

### 1. Stage changes

```bash
git add .
```

Or if the user specified files, stage only those.

### 2. Review staged diff

```bash
git status
git diff --staged
```

Check:
- Only intended changes are staged
- No unrelated modifications sneaked in
- No obvious secrets, credentials, or personal information visible
- No files that should be gitignored (`.env`, `credentials.json`, etc.)

If anything looks wrong, stop and ask the user before proceeding.

### 3. Run privacy-guard agent

Invoke the privacy-guard agent with just "scan this repo" — nothing
more. Do NOT tell it what to scan, how to scan, or what to look for.
The agent has its own instructions and will determine scope on its own.

If the agent reports any findings with severity `high` or `medium`,
**stop and report the findings to the user**. Do not commit until the
user addresses them or explicitly approves committing with known
findings.

If the agent reports `partial` status (untracked files), warn the user
but allow the commit to proceed — untracked files won't be in the
commit.

### 4. Commit

If the user provided a commit message, use it. Otherwise, draft one:
- Summarize the nature of the changes (new feature, bug fix, refactor)
- Focus on the "why" not the "what"
- Keep it concise (1-2 sentences)

```bash
git commit -m "<message>"
```

### 5. Post-commit

Report success. If the user said "push" or "commit and push", remind
them to push manually — this skill does not push.

## When privacy-guard is not available

If the privacy-guard agent is not installed or fails to run, fall back
to manual review only (steps 1-2) and warn the user that the automated
privacy scan was skipped. Do not silently skip the scan.
