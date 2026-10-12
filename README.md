# claude-coding

Claude Code plugin providing a default `claude-coder` agent — privacy-gated
commits, session lifecycle, and composition with skills installed alongside
it — plus the `show-code` skill.

## What's included

### Agents

- **claude-coder** — default coding agent (activated by the plugin's
  `settings.json`). Its `skills:` frontmatter preloads the general skills it
  relies on — `safe-commit`, `author-github-issue`, `capture-context`,
  `sociable-unit-tests`, `project-docs` — plus this plugin's `show-code`.

### Skills

- **show-code** — render a block of code in chat with the right filetype
  for inline reference.

## General skills come from echoskill

The plugin does not redistribute general-purpose skills. `safe-commit` (with
its bundled privacy reviewer), `author-github-issue`, `capture-context`, and
the rest live in [echoskill](https://github.com/echo-skill/echoskill).
Install them from there — or save them to your Claude account — and
`claude-coder` preloads them by name.

**Install each skill through one channel only.** A skill delivered through
two channels (for example a marketplace plugin and an account save) loads
twice.

## Install

```bash
claude plugin marketplace add https://github.com/echomodel/claude-plugins.git
claude plugin install claude-coding@echomodel --scope user
```

## Repository structure

The repo root **is** the plugin. No build step, no generated output.

```
.claude-plugin/plugin.json    <- manifest and version
agents/                       <- agent definitions
skills/                       <- skills native to this plugin
settings.json                 <- default agent activation
.mcp.json                     <- MCP server config (empty by default)
tests/                        <- lint + plugin-load tests
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

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository layout,
testing, and the release workflow.
