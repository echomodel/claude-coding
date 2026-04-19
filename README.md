# claude-coding

Claude Code plugin providing privacy-gated commits, the `privacy-guard`
and `privacy-audit` agents, and a default `claude-coder` agent that
composes with skills installed alongside it.

## What's included

### Agents

- **privacy-guard** — pre-push PII scanner (staged, unstaged, unpushed).
- **privacy-audit** — full-repo PII audit (git history, optionally issues/PRs).
- **claude-coder** — default coding agent with the privacy-gated commit
  workflow.

### Skills

- **safe-commit** — commit-first workflow with a privacy-guard scan
  gate. Native to this plugin because it invokes the `privacy-guard`
  agent.
- **show-code** — render a block of code in chat with the right
  filetype for inline reference.

The plugin does not redistribute general-purpose coding skills. The
`claude-coder` agent's `skills:` frontmatter names skills like
`author-github-issue`, `capture-context`, and `sociable-unit-tests`;
those come from the [echoskill](https://github.com/echo-skill/echoskill)
marketplace. Install echoskill alongside this plugin if you want those
skills preloaded.

## Privacy Guard Agent

An AI agent that scans repositories for personal information leaks.
Unlike regex-based scanners, privacy-guard reasons about context — it
catches things no pattern matcher can.

- Pattern-based detection from configurable PERSON.md
- OS-level discovery (`$USER`, `$HOME`) at runtime
- Judgment-based detection of contextual leaks
- Git author identity and visibility-aware scan tiers
- Read-only by design — cannot modify your repository

See [docs/agents/privacy-guard/](docs/agents/privacy-guard/README.md)
for full documentation including scan scope, detection categories,
containment model, and output schema.

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

## Install as plugin

```bash
claude plugin marketplace add https://github.com/echomodel/claude-plugins.git
claude plugin install claude-coding@echomodel --scope user
```

## Standalone agents (no plugin required)

Clone and install any agent in two commands — no plugin, no venv, no
dependencies beyond Python 3:

```bash
git clone https://github.com/echomodel/claude-coding.git
cd claude-coding
./agent install privacy-guard
```

The agent is now available globally:

```bash
claude --agent privacy-guard -p "scan this repo"
```

The agent can scan any repo — just `cd` into it and run. To grant
access to directories outside the repo:

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
| `privacy-guard` | Pre-push PII scanner — staged diffs, unstaged diffs, unpushed commits |
| `privacy-audit` | Full-repo PII audit — git history, optionally issues/PRs |

### Testing agents

See [docs/AGENT-CLI.md](docs/AGENT-CLI.md) for full `./agent` CLI
documentation including install, test, filtering, parallelism, and
debug logging.

```bash
./agent test privacy-guard
./agent test privacy-guard -k test_email_in_staged_file
./agent test privacy-guard -n 5 --debug
```

## Repository structure

The repo root **is** the plugin. No build step, no generated output.

```
.claude-plugin/plugin.json    <- manifest and version
agents/                       <- agent definitions
skills/                       <- native skills (depend on this plugin's machinery)
hooks/                        <- lifecycle hooks
settings.json                 <- default agent activation
.mcp.json                     <- MCP server config (empty by default)
agent                         <- standalone-agent CLI
tests/                        <- lint + integration tests
docs/                         <- agent documentation
```

Marketplace entries use `path: "."` — the clone IS the installable
plugin.

## Awareness of related plugins

claude-coding carries ambient awareness of adjacent first-party
plugins so the user doesn't need them resident in every Claude Code
session to benefit from their existence. When a session calls for
capabilities those other plugins provide, the default agent knows to
point at the right plugin and guide installation into the specific
project where it's needed — keeping unrelated sessions lean.

The canonical example is [claude-plugin-creator](https://github.com/echomodel/claude-plugin-creator):
when the user asks to create, scaffold, or author a new Claude Code
plugin, the default agent recommends installing claude-plugin-creator
at **project scope** in the plugin's repo rather than user scope. That
way its patterns and workflow guidance are loaded only when working
on the plugin, not in every coding session.

## Release workflow

```bash
# 1. Bump version in .claude-plugin/plugin.json

# 2. Test
pytest tests/lint/

# 3. Commit, tag, push
git add -A
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags

# 4. Update the marketplace entry's ref to the new tag, commit and push
#    the marketplace repo, then reinstall the plugin.
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture details,
testing, and development workflow.
