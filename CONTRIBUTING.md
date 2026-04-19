# Contributing

## FAQ

**Why don't we copy the agent to `~/.claude/agents/` for testing?**
That creates a sync problem — the copy can drift from the source in
`agents/`. Every change would require a re-copy. Instead, tests
create a symlink from each temp repo's `.claude/agents/privacy-guard.md`
back to the source file. Claude discovers it via local project scope. The
test always runs against the current source. See "How agent tests work"
under Testing.

**Why don't tests use `--plugin-dir` to load the agent?**
We don't want tests to depend on the full plugin being functional. The
agent should be testable in isolation. The symlink approach tests the
agent directly without plugin discovery, marketplace install, or any
other machinery.

**What's the difference between `skills/` and `.claude/skills/`?**
`skills/` contains skills shipped with this plugin because they depend
on the plugin's machinery (e.g., `safe-commit` invokes the
`privacy-guard` agent). `.claude/skills/` is for developing this repo
— project-level skills only available when you open a Claude session
here. They are never shipped.

**Does the plugin inject context into repos that install it?**
The plugin's root CLAUDE.md is for developing the plugin itself — it
does NOT load into other repos. How plugins inject context into
consumer repos (if at all) is an open question. Plugins definitely
provide skills, agents, hooks, and MCP servers. Whether there's a
context injection mechanism beyond those needs investigation against
Claude docs and the `claude-plugin-creator` repo.

**Can users run `claude --agent privacy-guard` from the CLI?**
Yes — if the agent is in `~/.claude/agents/` (user scope) or
`./.claude/agents/` (project scope), use the bare name. If loaded
via a plugin, use the namespaced form:
`--agent claude-coding:privacy-guard`.

## Repository structure

The repo root **is** the plugin. No build step, no generated output,
no assembly. A marketplace entry points at `path: "."` and the clone
is immediately the installable plugin.

```
claude-coding/
  .claude-plugin/
    plugin.json       <- manifest and version (single source of truth)
  agents/
    privacy-guard.md  <- standalone-usable reusable agent
    privacy-audit.md  <- standalone-usable reusable agent
    claude-coder.md   <- plugin-scoped (depends on safe-commit -> privacy-guard)
  skills/
    safe-commit/      <- native (depends on privacy-guard agent)
    show-code/        <- native
  hooks/
    hooks.json
    post-scan-verify.py
  settings.json       <- default agent activation
  .mcp.json           <- MCP server config (empty by default)
  agent               <- standalone-agent CLI, reads agents/ directly
  tests/              <- lint + integration tiers
  docs/               <- agent documentation
  README.md
  CONTRIBUTING.md
```

### Directory roles

| Directory | Role |
|-----------|------|
| `agents/` | Agent definitions — all of them. |
| `skills/` | Skills shipped with the plugin because they depend on its machinery. |
| `hooks/` | Lifecycle hooks and their scripts. |
| `.claude-plugin/` | Plugin manifest. |
| `tests/` | Lint and integration tests. |
| `docs/` | Agent design and CLI documentation. |
| `.claude/` | Development-only configuration for working on this repo — skills, project settings. Never ships. |

### What goes where

| Content | Belongs in |
|---------|-----------|
| Agent definition | `agents/*.md` |
| Skill that depends on this plugin's agents or hooks | `skills/*/SKILL.md` |
| Plugin config (plugin.json, settings.json, hooks, .mcp.json) | Repo root / `.claude-plugin/` / `hooks/` |
| Dev-only skills (testing, validation) | `.claude/skills/*/SKILL.md` |
| How to use the plugin | `README.md` |
| Architecture, testing, dev workflow | `CONTRIBUTING.md` |
| `@` imports of README + CONTRIBUTING | `CLAUDE.md` (root) |

### What this plugin does NOT redistribute

General-purpose coding skills (`author-github-issue`,
`capture-context`, `sociable-unit-tests`, etc.) live in the
[echoskill](https://github.com/echo-skill/echoskill) marketplace, not
in this plugin. The `claude-coder` agent's `skills:` frontmatter
names some of those skills for preloading; they resolve from
wherever the user has them installed (typically echoskill).

Bundling general skills into this plugin would be an
"alt marketplace install" — users who already have echoskill would
see duplicate entries in slash menus. A plugin should bundle only
skills that cannot function without its machinery. See the
`skill-author` skill in echoskill for the full "avoiding duplicate
installs" guidance.

### Reusable vs plugin-scoped agents

An agent is reusable if it works standalone without depending on this
plugin's skills, hooks, or other agents. `privacy-guard` and
`privacy-audit` are reusable — they scan independently.

`claude-coder` is plugin-scoped — its `skills:` frontmatter references
`safe-commit`, which invokes `privacy-guard`, creating a dependency
chain that only works with this plugin installed.

All three live in `agents/`. The reusable ones can also be installed
standalone via `./agent install <name>`.

## Testing

Two test tiers:

### Lint (default, fast)

```bash
pytest tests/lint/
```

Static validation of source files:
- Agent `.md` files have valid frontmatter (name, description)
- Skill SKILL.md files have valid frontmatter and matching directory name
- Plugin config files exist and are valid JSON
- `settings.json` agent ref resolves to a real agent file

### Integration tests (privacy-guard / privacy-audit agents)

These spawn real agent processes against temporary git repos with
planted PII and verify structured JSON output. Each test takes 1-3
minutes.

```bash
# Run one test at a time (recommended during development)
./agent test privacy-guard -k <test_name>

# Run all in parallel (full regression)
./agent test privacy-guard
```

Set `PRIVACY_GUARD_DEBUG=1` to write per-test logs to
`/tmp/privacy-guard-tests/`. Each test produces a harness log
(`<repo>.log`) and a Claude debug log (`<repo>.claude-debug.log`).
Watch in real time: `tail -f /tmp/privacy-guard-tests/*.log`

Integration tests are excluded from default `pytest` runs via
`pytest.ini`. They only run when explicitly targeted.

The `debug-agent-tests` project skill (`.claude/skills/`) has
the recommended test execution order and failure diagnosis steps.

#### How agent tests work (symlink isolation)

The agent source lives in `agents/privacy-guard.md`. Integration
tests need to invoke this agent via `claude --agent privacy-guard`, but
without:

- Installing the plugin (via marketplace or `--plugin-dir`)
- Copying the agent to `~/.claude/agents/` (creates a sync problem)
- Depending on any plugin machinery to resolve the agent

Claude resolves `--agent <name>` by looking in:
1. `~/.claude/agents/<name>.md` (user scope)
2. `./.claude/agents/<name>.md` (local project scope)

The test harness exploits option 2. For each test, `conftest.py`:

1. Creates a temporary git repo in an OS-managed temp directory
2. Creates `.claude/agents/` inside that temp repo
3. Symlinks `.claude/agents/privacy-guard.md` → the source file at
   `<repo>/agents/privacy-guard.md`
4. Runs `claude --agent privacy-guard -p "..."` with `cwd` set to
   the temp repo

When Claude starts in the temp repo directory, it discovers the agent
via the local `.claude/agents/` path. The symlink guarantees the test
always runs against the **current source code** of the agent — edits
to `agents/privacy-guard.md` are immediately reflected in the next
test run without any copy, sync, or install step.

This approach:

- **Isolates each test** — every test gets its own temp repo with its
  own `.claude/agents/` symlink, independent of all other tests
- **Tests the real agent** — the symlink points to the actual source
  file, not a copy or fixture
- **Has no external dependencies** — doesn't need the plugin installed,
  doesn't need `~/.claude/agents/` populated, doesn't need `--plugin-dir`
- **Works in parallel** — each test's temp dir is unique (pytest
  `tmp_path`), so parallel workers don't collide
- **Cleans up automatically** — pytest removes temp dirs after the run

#### What the tests use (fictitious data)

Tests do NOT use real personal information. The test PERSON.md contains
obviously fictitious values (`Zanzibar Quuxington`, `Xyzzy Bank`,
`Frobnitz Manor`) that will never collide with real PII on any machine
or trigger real privacy scanners. The agent treats the file as real —
it has the same structure and YAML frontmatter as a real PERSON.md but
with no "this is a test" hints that might cause the agent to behave
differently.

#### Template repo and PII injection

Tests use a template repo (`tests/fixtures/template_repo/`) containing
~20 clean Python files — a realistic widget service with models, API
handlers, tests, config, and docs. Each test copies the template into
a temp git repo, then injects PII into specific locations (staged
files, unstaged modifications, commit messages, code comments, config
files, test fixtures).

Credentials and secrets in the test code are built via string
concatenation at runtime (`"ghp_" + "a" * 36`) so precommit scanners
don't flag the test code itself.

#### Why privacy-guard and privacy-audit are separate agents

They are separate agents rather than modes of one agent. Claude Code
agents receive inputs only through the prompt (unstructured text),
the agent `.md` definition (static), and files the agent reads at
runtime. There is no structured input contract — no typed parameters,
no schema for inputs.

In testing we observed that the prompt can override config file
settings (a parent agent requesting "deep scan" overrode the user's
`pre-push` config). Until Claude Code supports formal agent input
schemas, splitting by usage pattern is more reliable than runtime
parameterization.

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

## Agent definitions

Agent `.md` files live in `agents/`. All are automatically discovered
when the plugin is installed.

Plugin agents cannot use `hooks`, `mcpServers`, or `permissionMode`
frontmatter (security restriction). Agents that need hooks must be
installed to `~/.claude/agents/` separately (the `./agent install`
CLI covers this for reusable agents).

### Memory settings

Each agent can have a `memory` field in its frontmatter (`user`,
`project`, `local`). Memory settings are intentional — each agent's
memory scope is decided case-by-case based on whether the agent should
learn and what scope that learning applies to.

## Safety architecture

Three reinforcement layers protect against accidental PII exposure:

1. **Agent definitions** — privacy-guard scans diffs and unpushed
   commits with LLM judgment. Built-in patterns catch credentials
   and secrets. Employer context table catches contextual leaks.
2. **Plugin hooks** — PostToolUse(Agent) verifies subagent input/output.
   PreToolUse(Bash) blocks uncertified pushes. See
   `docs/design/scan-cert-chain.md`.
3. **Deterministic scanners** — git pre-commit hooks (consult precommit,
   git-scan) catch known patterns with regex. Defense in depth.

### Subagent containment principle

The privacy-guard agent exists to **contain** PII exposure. It reads
PERSON.md so the parent agent doesn't have to. The containment boundary
is between what the agent **scanned for** (the universe of sensitive
values from PERSON.md, OS discovery, built-in patterns) and what it
**found** (specific values that already exist in the repo). These two
categories have opposite output rules.

**Matched values: MUST be reported.** The parent agent already has
access to these values — they are in the code, commits, issues, or
other artifacts the parent can see. The parent agent is responsible
for fixing them, which it cannot do without knowing the specific value
and its location. Reporting a matched value also makes the parent
agent less likely to repeat it in the same session — being told "this
email in src/config.py:42 is PII" is a corrective signal.

**Scan targets: MUST NOT be reported.** The full set of values the
agent checked for — every email, name, financial provider, etc. from
PERSON.md — must never appear in the output. The parent agent has no
need for these values and may not even be aware they exist. Exposing
them expands the parent's knowledge of the user's personal information
beyond what is already in the repo, increasing the risk of accidental
inclusion in commits, issues, PR descriptions, or conversation.

**Rules for subagent output:**

- **Never echo PERSON.md contents** — the agent already has this rule
  (Hard Rules in the agent definition). The structured JSON and
  human-readable report must not include the patterns being scanned
  for, only the values that were actually found.
- **Findings include matched values and locations** — a finding says
  "found email `user@example.com` in src/config.py:42". The parent
  needs both the value and the location to take action.
- **Scan metadata reports counts and sources, not values** — the
  structured output should include metadata about what categories were
  scanned, how many values per category, and where those values came
  from (PERSON.md frontmatter, PERSON.md body, OS runtime, prompt,
  built-in patterns). It reports **counts and sources only**. For
  example: `{"category": "emails", "values_count": 3, "source":
  "person_md_frontmatter"}` — not the actual email addresses that
  were searched for.
- **Attribution per finding** — each finding should indicate where the
  agent learned that the matched value was sensitive: `person_md_frontmatter`,
  `person_md_body`, `prompt`, `builtin_pattern`, `os_runtime`, or
  `contextual_judgment`.
- **The parent agent context is the threat model** — any value in the
  subagent's output enters the parent agent's context window. Matched
  values are already in the parent's accessible scope (the repo), so
  reporting them adds no new exposure. But scan targets from PERSON.md
  may include values the parent has never seen — family names not in
  any code, financial providers with no repo reference, etc. Leaking
  those expands the parent's PII surface for no benefit.

### Safety rules for interactive sessions

When working on this repo interactively (not through an agent):

- **Run privacy-guard before pushing.** Use `/safe-commit` or invoke
  the privacy-guard agent directly.
- **Review the scan output** before pushing. The agent reports findings
  with matched values and locations.
