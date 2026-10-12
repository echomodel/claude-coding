# Contributing

## FAQ

**What's the difference between `skills/` and `.claude/skills/`?**
`skills/` contains skills shipped with this plugin. `.claude/skills/` is
for developing this repo — project-level skills only available when you
open a Claude session here. They are never shipped.

**Why isn't `safe-commit` in `skills/`?**
It is a general skill with its own bundled privacy reviewer, so it lives in
[echoskill](https://github.com/echo-skill/echoskill) and installs from there
(or from a Claude account save). `claude-coder` preloads it by name. Shipping
it here too would deliver one skill through two channels.

**Does the plugin inject context into repos that install it?**
The plugin's root CLAUDE.md is for developing the plugin itself — it
does NOT load into other repos. How plugins inject context into
consumer repos (if at all) is an open question. Plugins definitely
provide skills, agents, hooks, and MCP servers. Whether there's a
context injection mechanism beyond those needs investigation against
Claude docs and the `claude-plugin-creator` repo.

## Repository structure

The repo root **is** the plugin. No build step, no generated output,
no assembly. A marketplace entry points at `path: "."` and the clone
is immediately the installable plugin.

```
claude-coding/
  .claude-plugin/
    plugin.json       <- manifest and version (single source of truth)
  agents/
    claude-coder.md   <- default agent; preloads general skills by name
  skills/
    show-code/        <- native
  settings.json       <- default agent activation
  .mcp.json           <- MCP server config (empty by default)
  tests/              <- lint + plugin-load tests
  README.md
  CONTRIBUTING.md
```

### Directory roles

| Directory | Role |
|-----------|------|
| `agents/` | Agent definitions. |
| `skills/` | Skills shipped with the plugin. |
| `.claude-plugin/` | Plugin manifest. |
| `tests/` | Lint and plugin-load tests. |
| `.claude/` | Development-only configuration for working on this repo — skills, project settings. Never ships. |

### What goes where

| Content | Belongs in |
|---------|-----------|
| Agent definition | `agents/*.md` |
| Skill that only makes sense with this plugin | `skills/*/SKILL.md` |
| Plugin config (plugin.json, settings.json, .mcp.json) | Repo root / `.claude-plugin/` |
| Dev-only skills (testing, validation) | `.claude/skills/*/SKILL.md` |
| How to use the plugin | `README.md` |
| Architecture, testing, dev workflow | `CONTRIBUTING.md` |
| `@` imports of README + CONTRIBUTING | `CLAUDE.md` (root) |

### What this plugin does NOT redistribute

General-purpose skills (`safe-commit`, `author-github-issue`,
`capture-context`, `sociable-unit-tests`, etc.) live in the
[echoskill](https://github.com/echo-skill/echoskill) marketplace, not
in this plugin. The `claude-coder` agent's `skills:` frontmatter
names some of those skills for preloading; they resolve from
wherever the user has them installed.

Bundling general skills into this plugin would be an
"alt marketplace install" — users who already have echoskill would
see duplicate entries in slash menus. A plugin should bundle only
skills that cannot function without it. See the `skill-author` skill
in echoskill for the full "avoiding duplicate installs" guidance.

## Testing

### Setup (one-time)

```bash
python3 -m venv .venv
.venv/bin/pip install pytest pyyaml
```

The `.venv/` directory is gitignored.

### Lint (default, fast)

```bash
.venv/bin/pytest
```

Bare `pytest` runs the lint tier only — `pytest.ini` ignores
`tests/integration/` by default.

Static validation of source files:
- Agent `.md` files have valid frontmatter (name, description)
- Skill SKILL.md files have valid frontmatter and matching directory name
- Plugin config files exist and are valid JSON
- `settings.json` agent ref resolves to a real agent file

### Plugin load (integration)

```bash
.venv/bin/pytest tests/integration/plugin/
```

Starts Claude Code with `--plugin-dir` pointed at this repo and checks that
the plugin's own skills are discoverable.

## Release workflow

```bash
# 1. Bump version in .claude-plugin/plugin.json

# 2. Test
pytest

# 3. Commit, tag, push
git add -A
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags

# 4. Update the marketplace entry's ref to the new tag, commit and push
#    the marketplace repo, then reinstall the plugin.

# 5. Verify the release landed.
claude plugin marketplace update <marketplace-name>
claude plugin update claude-coding@<marketplace-name>
# Confirm the active install path points at the new version:
grep -A4 '"claude-coding@' ~/.claude/plugins/installed_plugins.json
# Expected: "installPath" ends in /<new-version> and "version" is the new tag.
```

`installed_plugins.json` is the source of truth for which version a
new session loads. Old version directories under
`~/.claude/plugins/cache/<marketplace>/claude-coding/` are leftover
artifacts and do not indicate the active version — never infer the
active version from those paths.

## Agent definitions

Agent `.md` files live in `agents/`. All are automatically discovered
when the plugin is installed.

Plugin agents cannot use `hooks`, `mcpServers`, or `permissionMode`
frontmatter (security restriction).

### Memory settings

Each agent can have a `memory` field in its frontmatter (`user`,
`project`, `local`). Memory settings are intentional — each agent's
memory scope is decided case-by-case based on whether the agent should
learn and what scope that learning applies to.
