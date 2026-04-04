---
name: pre-publish-privacy-review
description: >-
  Review all session work for personal information, sensitive data, and private
  details that should not be in public-facing artifacts. Use before pushing,
  publishing, or ending a session — or when the user says "check for personal
  info", "PII review", "privacy check", or "did I leak anything personal".
disable-model-invocation: true
---

# Pre-Publish Privacy Review

Review everything the agent touched or created during this session — with human
judgment, not regex — to find personal or sensitive information that does not
belong in public-facing artifacts.

This is NOT a deterministic scanner. Precommit hooks and repo scanners handle
pattern matching. This skill asks the agent to think critically about context:
"Given what I know about this user and this session, did I put anything
personal, identifying, or user-specific into a place where it should not be?"

## What to Review

Examine every artifact the agent created or modified during this session:

- **Versioned files** — code, configuration, documentation, `.md` files,
  examples, code comments, docstrings, help text, error messages
- **Commit messages** — every commit made during this session
- **GitHub issues** — titles, bodies, and comments created or edited
- **Unpushed commits** — review staged and committed content that has not yet
  been pushed, as this is the last chance to fix it cheaply
- **Commits made early in the session** — these are easy to forget; the agent
  may have been less careful before the user raised concerns

For each artifact, consider the repo's visibility. Public repos and private
repos without a `personal-` prefix require strict rules. Private repos with a
`personal-` prefix allow PII but still prohibit credentials.

## What to Look For

The agent has context that no regex can match. Use it. Look for:

| Category | What to catch |
|----------|---------------|
| **Real names** | The user's name, family members, colleagues — anywhere in code, comments, docs, commit messages, or issues |
| **Email addresses** | Real email addresses (not `user@example.com` placeholders) |
| **Usernames** | OS login names, GitHub usernames, account handles that identify the user |
| **Workspace paths** | Absolute paths containing usernames (`/home/user/...`), workstation-specific workspace roots. These break portability and reveal identity |
| **Cloud/service IDs** | GCP project IDs, Google Doc/Sheet/Drive IDs, API client IDs — anything that ties to a specific account |
| **Personal use cases** | References to the user's personal workflow, personal projects that consume the repo, or reasons the user needs a feature that reveal their identity as a user of the repo |
| **Employer/org references** | The user's employer name in a context that identifies them (not as a tech provider — "Google Gemini API" is fine, "my employer's SSO" is not) |
| **Financial data** | Real dollar amounts, account numbers, tax identifiers |
| **Credentials** | API keys, tokens, secrets — even if they look like they might be test values, flag them |
| **Session artifacts** | Session IDs, resume commands, agent conversation references — these belong only in private locations |

### The judgment call

A deterministic scanner flags `ghp_abc123` as a GitHub token. That is easy.
The hard part — and the reason this skill exists — is catching things like:

- A commit message that says "fix the bug Bob reported" instead of "fix
  input validation bug"
- An issue body that says "I need this for my food tracking app" instead of
  "applications that log structured data need..."
- A code comment with `# TODO: ask $COLLEAGUE about this`
- An example that uses a real Google Doc ID from the session
- A file path in documentation that reveals the user's workspace layout
- A description that frames a feature in terms of the user's personal need
  rather than the repo's general purpose

These require understanding who the user is and what details are personal.
The agent has that context from the session. Use it.

## Report Format

Present findings as a list grouped by severity:

### Must fix before push

Items that contain clearly personal or sensitive information in a public-facing
artifact. For each, state:
- What was found and where (file:line, commit SHA, issue number)
- What it should be replaced with
- Whether it requires rewriting a commit message (which needs interactive
  rebase or amend)

### Worth reviewing

Items that might be personal depending on context the the agent is uncertain
about. For each, state what was found and why it might be a concern.

### Clean

Artifacts reviewed and found to have no issues. List them briefly so the user
can see the scope of the review.

## Fixing Findings

After presenting findings, propose specific fixes and ask for permission.
For committed content that has not been pushed, offer to amend or rewrite.
For content already pushed, note that the information is already in the remote
history and suggest what can still be done (force-push if appropriate, or
accept the exposure and fix going forward).

For GitHub issues, propose edits to the title or body.

Do not silently fix anything — always show the user what will change.
