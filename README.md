# claude-coding-plugin

Claude Code plugin for autonomous, safety-gated coding work. Takes GitHub
issues as input, works in isolated worktrees, enforces privacy review on
every artifact, and gates all GitHub writes behind human approval.

## Two ways to use this

1. **As a plugin** — install once, get everything: agents, skills, hooks,
   safety gates. Agents appear in `/agents` during interactive sessions.
2. **As standalone agents** — clone the repo, run one command, use any
   agent from the CLI without installing the plugin.

## What's included

- **privacy-guard** — AI-powered PII and privacy scanner
- **refactoring-agent** — Issue-driven autonomous refactoring
- **publish-agent** — Clean-room branch reviewer and publisher
- **Skills** — publish-pull-request, privacy-scan, delegate-refactoring,
  check-feature-support, plus vendored coding skills from echoskill
- **Hooks** — Pre-push safety gates, test skill injection
- **Safety architecture** — Three-layer enforcement (hooks + agent prompts + skills)

## Privacy Guard Agent

An AI agent that scans repositories for personal information leaks.
Unlike regex-based scanners, privacy-guard reasons about context — it
catches things no pattern matcher can.

### What it scans

| Scope | Default | On request |
|-------|---------|------------|
| Working tree (tracked + untracked files) | Yes | |
| Staged changes | Yes | |
| Unpushed commits (messages + diffs) | Yes | |
| Open GitHub issues (titles, bodies, comments) | Yes | |
| Open GitHub PRs (titles, bodies, comments) | Yes | |
| Full git history (all commits, branches, tags) | | Yes |
| Stash entries and reflog | | Yes |
| Closed issues and PRs | | Yes |

### What it catches

**Pattern-based** — matches specific personal values you configure:

- Names (yours, family members, variants and nicknames)
- Email addresses and personal email domains
- Phone number area codes
- Custom/personal domains
- Financial service providers (banks, brokerages)
- Employer references and employer-specific terms
- Property names and associated locations
- GitHub username in non-self-referential contexts
- Private repo names referenced from public repos
- Workspace root paths and contributor-specific local paths

**OS-discovered at runtime** — no configuration needed:

- OS username (from `$USER`)
- Home directory path (from `$HOME`)

**Judgment-based** — contextual leaks that no regex can catch:

- A commit message that says "fix the bug Alice reported" instead of
  "fix input validation bug"
- An issue body that says "I need this for my food tracking app"
  instead of "applications that log structured data need..."
- A README that frames a project as "built for tracking my rental
  properties" instead of "a property management tool"
- Example code that uses a real Google Doc ID from a recent session
- Test fixtures populated with real family member names
- Documentation that reveals which personal products consume the repo

**Git author identity checks:**

- Commit author matching git config: expected, not flagged
- Same name/email in commit messages, file content, or issues: flagged
- Author email domain mismatch across commits (e.g., work email in
  personal repo or vice versa): flagged

**Repo visibility awareness:**

- Public repos and non-`personal-` private repos: STRICT — all
  categories flagged
- Private repos matching a configurable "personal" prefix: RELAXED —
  only true secrets (passwords, API keys, SSNs, private keys)

### Structured JSON output

Every scan produces a machine-parseable JSON block alongside the
human-readable report. Automated callers (other agents, CI, test
harnesses) can parse findings programmatically. Categories and
location types use suggested values for consistency but are open
strings — the agent can report findings that don't fit predefined
categories.

### Prerequisite: personal patterns file

Before first use, create `~/.config/ai-common/PERSON.md` with your
personal information. The agent reads this file to know what to scan
for. Without it, the agent refuses to run.

The file uses YAML frontmatter for machine-parseable patterns:

```yaml
---
patterns:
  github:
    - your-github-username
  emails:
    - your-email@example.com
  email_domains:
    - your-domain.com
  names:
    - Your Name
    - Spouse Name
    - Child Name
  workspace_roots:
    - ~/src
    - ~/projects
  financial_providers:
    - Your Bank
  employers:
    - Your Employer
  properties:
    - Property Name
  cities:
    - Your City
---
```

A markdown body below the frontmatter provides judgment guidance —
false positive rules, employer-specific detection nuances, financial
amount thresholds, and context for city/property names that are also
common words.

The agent discovers OS-level identifiers (username, home directory)
at runtime — those do not go in this file.

**This file must never be committed to any repository.** It lives
only on your machine.

### Read-only by design

The agent cannot modify your repository. Its tool allowlist is locked
to read-only operations: `Read`, `Grep`, `Glob`, read-only `git`
commands, and read-only `gh` commands. No `Write`, `Edit`, `git push`,
`gh issue create`, or any other write operation is permitted. It
reports findings and stops.

## Install as plugin

```bash
claude plugin marketplace add https://github.com/krisrowe/claude-plugins.git
claude plugin marketplace update claude-plugins
claude plugin install claude-coding-plugin@claude-plugins --scope user
```

### Quick start

```
/delegate-refactoring owner/repo#42
```

The refactoring agent will:
1. Read the issue
2. Create an isolated worktree
3. Make changes, write tests
4. Prepare PULL-REQUEST.md
5. Run privacy scan
6. Present everything for your review
7. On approval, hand off to publish-agent for merge + push

## Standalone agents (no plugin required)

Clone and install any agent in two commands — no plugin, no venv, no
dependencies beyond Python 3:

```bash
git clone https://github.com/krisrowe/claude-coding-plugin.git
cd claude-coding-plugin
./agent install privacy-guard
```

The agent is now available globally:

```bash
claude --agent privacy-guard -p "scan this repo"
```

The agent can scan any repo — just `cd` into it and run. To grant
access to directories outside the repo (e.g., a sibling project):

```bash
cd ~/src/my-project-a
claude --agent privacy-guard --add-dir ~/src/my-project-b -p "scan both this repo and ~/src/my-project-b"
```

If the plugin is already installed, `./agent install` will warn you
that the agent is redundant (use `--force` to install anyway for CLI
`--agent` usage).

**Project-local install** (`--local`) installs the agent to a single
repo's `.claude/agents/` instead of user scope. This is rarely
needed — the user-scope install already works from any directory. The
only case is if you want the agent available for one specific repo and
don't want it showing up in the global agent list:

```bash
./agent install privacy-guard --local ~/src/my-only-project-i-care-about
```

### All agents

| Agent | Description |
|-------|-------------|
| `privacy-guard` | Read-only PII scanner — scans files, commits, issues, PRs |
| `refactoring-agent` | Autonomous issue-driven refactoring in isolated worktrees |
| `publish-agent` | Clean-room branch review and merge+push |

### Testing agents

```bash
# Run all tests for an agent
./agent test privacy-guard

# Run a single test
./agent test privacy-guard -k test_email_in_file

# Run in parallel (5 workers)
./agent test privacy-guard -n 5

# With debug logging (logs to /tmp/privacy-guard-tests/)
./agent test privacy-guard --debug -k test_missing_person_md
```

Watch debug logs in real time:

```bash
tail -f /tmp/privacy-guard-tests/*.log
```

The test venv (`.venv-test/`) is auto-created on first run.

## Build

See [CONTRIBUTING.md](CONTRIBUTING.md) for build process, context file
architecture, and development workflow.
