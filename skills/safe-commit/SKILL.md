---
name: safe-commit
description: >-
  Stage, review, scan, commit, and optionally push changes safely. Use
  EVERY TIME the user says "commit", "git commit", "push", "git push",
  "stage and commit", "commit this", "commit all", "commit and push",
  "safe commit", "ready to commit", "let's commit", or any variation
  of committing or pushing code. Also use when you (the agent) decide
  to commit on the user's behalf after completing a task.
user-invocable: true
argument-hint: "[commit message]"
---

# Safe Commit

Commit first, scan after, push only if clean. The commit happens
BEFORE the privacy scan because the scan needs to see the final commit
content including the commit message.

## Before you begin: single commit or multiple?

The default is **one commit per unit of work** — a coherent change
with one reason to exist. Don't manufacture splits.

A split into multiple commits is appropriate when:

- The user explicitly asks for separate commits.
- The working tree contains genuinely independent pieces of work
  (different features, different subjects, or unrelated fixes).

When splitting, these rules are absolute:

### Rule 1 — Split only at file boundaries

Each candidate commit must involve an **entirely separate set of
files** from the others. No file appears in more than one commit.
Whole-file granularity only.

Why: this is the only split method that preserves the property that
every commit's content was, at some point, the real state of files
on disk.

### Rule 2 — Never split via hunk surgery, stash, or temp edits

Do NOT use `git add -p` (interactive hunk staging), `git stash` +
re-apply, or temporary file edits to separate one file's changes
across multiple commits. Those techniques produce commits whose
content was never in the working tree as a coherent unit — nobody
tested that state, nobody wrote it, it exists only because of
surgery.

If a single file contains changes that conceptually belong to two
different commits, the honest options are:

- Commit them together as one commit (simplest, and safe).
- Revert the file, redo one change, commit, redo the other, commit
  (real states, real typing — but slow and error-prone).

Pick the first unless there's a strong reason.

### Rule 3 — Don't silently un-test a tested state

If tests have already been run on the combined working-tree state
(say, files A, B, C, D all changed together and tested as a unit),
then splitting into "commit with A+B" followed by "commit with
C+D" creates two commits that were **never tested in that form**.
The tested unit was all four files together. Each subset might
pass its own tests, might not — you don't know.

Safe options when testing has already happened on the combined
state:

- **Split only if the subset is obviously independent** of the
  rest (e.g., commit 1 touches pure test files renamed; commit 2
  adds a new unrelated script). "Obviously independent" means no
  shared import, no shared function, no shared config — a reviewer
  can confirm at a glance.
- **Re-test just the subset after splitting** — only if tests are
  fast, pure, and deterministic (seconds, local, unit-level). Stash
  the unrelated files, run tests, commit the tested subset, restore,
  repeat. Don't do this for slow or external-dependency tests —
  the retest cost usually exceeds the split benefit.
- **Give up and commit together.** This is almost always the right
  answer when in doubt. One "combined" commit that's coherent is
  better than two split commits whose individual correctness isn't
  verified.

When the user has asked for splits and you're unsure whether a
split honors Rule 3, SAY SO: explain the concern, ask whether to
split-and-retest, combine, or split-and-trust. Don't silently
pick.

### Rule 4 — Each commit must stand on its own

A reader who checks out any single commit in isolation should see
a coherent state. Broken-in-the-middle commits make `git bisect`
unusable and confuse future archaeology. "Stand on its own" doesn't
mean every commit is independently shippable — it means the
repository at that commit is syntactically valid, imports resolve,
and the commit represents a real state someone could have had.

### For multi-commit batches: scan once, at the end

The privacy-guard scan in Step 7 below is **per-push, not
per-commit**. When committing a batch of N separate commits, do
all N commits first (each via Steps 1–6), then run Step 7 ONCE
after the final commit. The scan evaluates the content of every
unpushed commit — one invocation covers the whole batch.

This matters for efficiency (scan takes real time / tokens) and
correctness (the scan sees the full set of commits it will be
pushing, not a partial view).

## Step 1: Check for gitignored violations

```bash
git status
```

Review the output. Are there files that SHOULD be gitignored but aren't?
Look for:
- `.env`, `credentials.json`, `secrets/`, `*.pem`, `*.key`
- `node_modules/`, `__pycache__/`, `.venv/`, `venv/`
- IDE files: `.idea/`, `.vscode/settings.json` (local, not shared)
- OS files: `.DS_Store`, `Thumbs.db`

If any should be gitignored, ask the user. Add them to `.gitignore`
and re-run `git status`. Repeat until clean.

## Step 2: Stage files individually

Do NOT use `git add .` — stage files by name:

```bash
git add <file1> <file2> ...
```

Stage only the files the user intends to commit. If unsure, ask.

Run `git status` again to confirm:
- Everything intended is staged
- Nothing unintended is staged
- No untracked files that should be staged or gitignored

If untracked files remain that aren't gitignored, ask the user: stage
them, gitignore them, or leave them (the scan will flag them).

## Step 3: Review staged diff

```bash
git diff --staged
```

Read the full diff. Check for:
- Secrets, credentials, API keys, tokens
- Personal information (names, emails, paths, employer references)
- Unintended changes mixed in
- Debug code, TODO comments with personal context

If anything looks wrong, stop and ask the user.

## Step 4: Confirm git hooks are active

```bash
git config core.hooksPath
```

If this returns a path (not empty), hooks are active and will scan on
commit. If empty or `/dev/null`, warn the user that no precommit
scanner will run — the commit proceeds without deterministic scanning.

## Step 5: Commit

Draft a commit message if the user didn't provide one:
- Summarize the nature of the changes (new feature, bug fix, refactor)
- Focus on the "why" not the "what"
- Keep it concise (1-2 sentences)

```bash
git commit -m "<message>"
```

If the precommit hook fails, review the findings. Fix issues and
retry. Do NOT use `--no-verify` unless the user explicitly approves.

## Step 6: Verify clean state

```bash
git status
```

Confirm:
- Working tree is clean (nothing dirty, nothing untracked that matters)
- Only unpushed commit(s) remain

If anything is dirty or untracked, go back to Step 1.

## Step 7: Run privacy-guard agent

**Run ONCE per push, not once per commit.** If you committed a
batch of N commits in this flow, do Steps 1–6 for each commit
first, then run this step a single time at the end. The scan
evaluates every unpushed commit in one invocation; running it
N times is pure waste.

The prompt for the agent is EXACTLY:

```
scan this repo
```

Do NOT add instructions about what to scan, how to scan, what to look
for, or any other context. The agent has its own instructions. Adding
to the prompt risks overriding the agent's behavior and will cause
the scan verification to fail.

### How to invoke: choose ONE path

privacy-guard reads `~/.config/ai-common/PERSON.md`, which lives
outside any project directory. The Agent tool route only works when
the parent Claude Code session was launched with access to that path
(e.g., `claude --add-dir ~/.config/ai-common`). The normal case —
session started inside a repo — has no such access, and the subagent
will fail with `person_md_not_found`. **Don't try the Agent tool
route and fall back; pick the right path up front.**

**Default path (terminal command).** When the parent session was
started in a project directory without `--add-dir ~/.config/ai-common`,
do NOT invoke the Agent tool. Instead, present this command for the
user to run in their own terminal:

```bash
cd <repo-path> && claude --agent privacy-guard --add-dir ~/.config/ai-common -p "scan this repo"
```

The user runs it; you read the JSON output they paste back (or, in
Claude Code, the command output appears in the conversation if
prefixed with `!`).

**Agent tool path (only if access is already granted).** If you can
verify the parent session has read access to `~/.config/ai-common/`
(e.g., the session was launched with `--add-dir ~/.config/ai-common`
or from `$HOME`), invoke the privacy-guard agent directly with the
prompt above. If unsure, default to the terminal command — guessing
wrong wastes a subagent invocation.

## Step 8: Interpret scan results

Parse the `privacy-guard-result` JSON from the agent's output.

The scan result is binary:

| Condition | Result | Action |
|-----------|--------|--------|
| `status: completed`, `findings` empty | **pass** | Offer push |
| `status: completed`, `findings` non-empty | **fail** | Show findings, no push, user must fix and recommit |
| `status: failed` | **fail** | Show error, no push |

No discretion. No partial. The content at this SHA either passes or
it doesn't. If there are findings, the user fixes them, amends or
creates a new commit (new SHA), and runs the flow again from Step 1.

## Step 9: Advise and offer push

**Pass:** Tell the user the scan passed. Ask if they want to push.

**Fail:** Show every finding. Tell the user what needs to be fixed.
Do NOT offer to push.

If the user believes a finding is a false positive, try workarounds
to avoid tripping it (reword, restructure, use placeholders). If no
workaround is possible, the user will need to obtain and install a
new release of the privacy-guard agent or the plugin and restart the
session.

## Step 10: Push (if approved)

Capture HEAD SHA and push that exact commit:

```bash
sha=$(git rev-parse HEAD)
git push origin $sha:refs/heads/$(git symbolic-ref --short HEAD)
```

Push the SHA, not HEAD — this prevents TOCTOU issues where HEAD moves
between the scan and the push.

## When privacy-guard is not available

If the privacy-guard agent is not installed or fails to run, tell the
user. No scan means no push. There is no fallback. Install the agent
and retry.

## If privacy-guard still fails with "person_md_not_found"

This means the user has not created `~/.config/ai-common/PERSON.md`,
or the path passed to `--add-dir` was wrong. See the
[claude-coding README](https://github.com/echomodel/claude-coding#prerequisite-personal-patterns-file)
for the PERSON.md format. Without that file, privacy-guard refuses
to run. No scan means no push.

## Post-push rescan

If commits were pushed without a scan — because the push happened in
an environment without scanning enabled, a newer agent version needs
to re-evaluate previously pushed content, or a push slipped through
due to permission or tooling gaps — use this workflow to retroactively
scan what was pushed.

### Setup

Create a temporary branch at the pre-push baseline, push it to
establish a remote tracking point, then merge main so the pushed
commits appear as "unpushed" relative to the branch's remote:

```bash
# Find the last commit that was on remote before the unscanned push
git log --oneline -10   # identify the baseline commit

# Create and push baseline branch
git checkout -b rescan-basis <baseline-sha>
git push -u origin rescan-basis

# Merge main — the pushed commits are now "unpushed" on this branch
git merge main
```

### Run the scan

The scan must be run by the user from a shell, not from within an
existing agent session (subprocesses may lack file permissions):

```bash
claude --agent privacy-guard --add-dir ~/.config/ai-common -p "scan this repo"
```

If the repo being scanned is different from the current working
directory, `cd` to it first. The `--add-dir ~/.config/ai-common`
grants access to PERSON.md (required for scanning). The prompt must
always be exactly "scan this repo" without modifications.

### Interpret and clean up

If the scan passes, clean up:

```bash
git checkout main
git branch -D rescan-basis
git push origin --delete rescan-basis
```

If the scan finds issues, the content is already pushed. Fix the
findings in a new commit on main, then push the fix. The rescan
branch can be deleted either way — it was only scaffolding to make
the already-pushed commits visible to the scanner.
