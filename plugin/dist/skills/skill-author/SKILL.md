---
name: skill-author
description: >-
  Guide for developing, validating, and publishing AI agent skills.
  Provides reliable steps to make, build, create, or develop a skill,
  to review or revise a skill, or to publish or register a new or
  updated skill either locally — installing it at project, user, or
  global scope for one or more agents — or to a central registry,
  marketplace, or repo. Use when writing a SKILL.md, setting up
  frontmatter, choosing where a skill belongs, or preparing a skill
  for distribution.
---

# Developing Portable Agent Skills

## Default Posture: Portability

Always aim for cross-platform skills unless there is a genuine reason a skill
can only work on one platform. Challenge assumptions about platform specificity:

- "Does this skill REALLY require Claude-only features, or can the instructions
  be written neutrally?"
- "Am I using platform-specific frontmatter out of habit or necessity?"

If the user says they're building for just one platform, evaluate whether the
skill's purpose is truly platform-specific by nature. Guide them toward portable
design when feasible.

## Skill Format: agentskills.io Standard

Skills use the [agentskills.io](https://agentskills.io/specification) open
standard, supported by 30+ tools (Claude Code, Gemini CLI, VS Code/Copilot,
Cursor, and many others).

A skill is a directory containing `SKILL.md` with YAML frontmatter:

```yaml
---
name: my-skill
description: When to invoke this skill and what it does
---

Instructions for the agent...
```

### Required Fields

- `name` — lowercase, hyphens, 1-64 chars, must match directory name
- `description` — up to **1024 characters** (agentskills.io spec). This
  field is for **discovery and selection only** — it tells agents and
  users *when* this skill applies and *what problem it solves*, not
  *how* it works.

  **Front-load the first 250 characters.** Claude Code truncates
  descriptions beyond 250 chars in the skill listing. Put the primary
  trigger and use case up front. Additional keywords and scenarios can
  follow after 250 chars — they're still available when the full
  description loads into context, just not visible in the listing.

  **Use imperative framing.** Include "Use when..." to tell the agent
  when to act. Agents are making a selection decision — tell them when
  to select this skill, not just what it is.

  **Cover synonyms and verb variants.** Users say the same thing many
  ways. A skill for building skills should say "make, build, create,
  develop" not just "create". A PDF skill should say "reading,
  extracting, combining, merging, splitting..." — enumerate the verbs.
  This is established best practice per agentskills.io: "err on the
  side of being pushy" and "include cases where the user doesn't name
  the domain directly."

  **Avoid disqualifying language.** The description gates selection.
  If it mentions a specific platform, an agent building for a different
  platform may skip it. If it says "portable" or "cross-platform", an
  agent building a platform-specific skill may skip it. Keep the
  description maximally inclusive — opinionated guidance (like "prefer
  portability") belongs in the body where it can be articulated with
  nuance, not in the gate where it's a binary filter.

  Example: a skill for building agent skills should NOT say "for Claude
  Code and Gemini CLI" in the description — an agent building a Cursor
  skill or a platform-specific skill would self-exclude. The body can
  then guide toward portability where appropriate.

  **Add negative triggers only when non-obvious.** "Don't use for Vue
  or Svelte projects" helps a CSS skill avoid false triggers. "Not for
  using existing skills" is obvious and only hurts invocation chances.
  If the boundary is clear from context, don't state it.

  **Do:**
  - Name the activity or situation that triggers it
  - Say what outcome the skill produces
  - Use "Use when..." imperative framing
  - Cover synonyms — enumerate the verbs and nouns users might say
  - Use the full 1024 chars if needed for thorough keyword coverage

  **Do NOT:**
  - Include implementation details (tool names, commands, file formats)
  - Include agent instructions ("read the file", "render in chat")
  - Describe the skill's internal workflow or steps
  - Mention specific platforms unless the skill is genuinely
    platform-specific by nature
  - Add negative triggers for boundaries that are already obvious
  - Repeat what belongs in the body of the SKILL.md

  The body of SKILL.md is where implementation details, agent
  instructions, rules, anti-patterns, and workflow steps go.

### Optional Fields (agentskills.io)

- `compatibility` — max 500 chars, environment requirements. Covers
  both system dependencies ("Requires git, docker, jq") and intended
  product ("Designed for Claude Code (or similar products)") per the
  spec's own examples. Use it when a skill genuinely requires specific
  tools, runtimes, or agent features. Don't add it reflexively when
  the skill works everywhere — most skills don't need this field.
- `metadata` — arbitrary key-value map for additional properties
- `allowed-tools` — space-delimited pre-approved tools (experimental)
- `license` — license name or reference to a bundled license file.
  Only include if the user suggests it.

### Platform Extension Fields

These are Claude Code extensions. Other agents silently ignore them.

- `disable-model-invocation: true` — user-only / slash-only, agent won't auto-invoke. Also blocks programmatic agent invocation via the Skill tool — only the user typing the slash command works.
- `user-invocable: false` — ambient-only, hidden from slash menu
- `allowed-tools: Bash, Read` — pre-approved tools
- `argument-hint: "[pattern]"` — autocomplete hint
- `context: fork` — run in isolated subagent
- `agent: Explore` — subagent type when `context: fork` is set
- `model` — model override when skill is active
- `effort` — effort level override (low/medium/high/max)
- `paths: "**/*.py"` — glob patterns limiting when skill activates
- `shell` — `bash` (default) or `powershell`
- `hooks` — skill-scoped lifecycle hooks

Using platform extension fields does not make a skill non-portable —
other agents silently ignore unknown fields. But if the skill *depends*
on a platform extension to function (e.g., `context: fork` is essential
to its operation), note that in `compatibility`.


## No Scripts in Skills

**Skills are pure instructions.** Do not bundle executable scripts.

Why:
- Gemini blocks `run_shell_command` by default. Enabling it is a blanket
  permission for ALL shell commands, not scoped to the skill. Unacceptable.
- Claude's `${CLAUDE_SKILL_DIR}` scripting works but has no Gemini equivalent
  for standalone skills. Portability breaks.

### What Skills CAN Do

- Reference MCP tools by name: "call the `gapp_deploy` tool"
- Describe commands the agent should run: "run `git status` on each repo"
- Include hints, examples, or templates for the agent to adapt
- Trust the agent to formulate execution plans with user approval

### When a Script Is Required

If a skill absolutely requires deterministic code execution — a specific script
that must run exactly as written — it is a candidate for a **plugin** (Claude)
or **extension** (Gemini), not a standalone skill. That's what the packaging
layer is for: MCP servers, hooks, bundled scripts, and dependency management.

## Marketplace Structure

Skills live in git repos organized as directories:

```
skills-repo/
├── prompting/              ← collection
│   ├── nm/SKILL.md
│   └── proceed/SKILL.md
├── coding/                 ← collection
│   ├── develop-skill/SKILL.md
│   └── develop-unit-tests/SKILL.md
└── claude/                 ← platform-specific collection
    └── sessions/SKILL.md
```

**Collection** = a folder of skill subfolders. Installable as a group:
```bash
gemini skills install <url> --path coding
```

Or individually:
```bash
gemini skills install <url> --path coding/develop-skill
aicfg skills install develop-skill
```

## Installation

Skills are installed via `aicfg skills install` (cross-platform) or
`gemini skills install` (Gemini native). Claude has no skill CLI — aicfg
writes directly to `~/.claude/skills/`.

Both tools discover skills by scanning directories for `SKILL.md` files.
No registration or manifest needed beyond the file itself.

## Writing Good Skill Instructions

- **Write for any agent by default.** Describe the desired outcome, not a
  tool-specific mechanism. Only target a specific agent platform when the
  user has explicitly said the skill is platform-specific.
- **Reference tools by name** when the skill depends on them (e.g., MCP tools).
  Note that the tool must be installed separately.
- **Include examples** of commands, workflows, or outputs the agent should
  produce. Agents perform better with concrete examples.
- **Keep it focused.** One skill, one purpose. If it does two unrelated things,
  split it into two skills.

## After Writing: Install, Test, Publish

Skills are fast-to-market by design. The goal is to impact the user's
workflow quickly — a skill sitting uninstalled helps no one. In most
cases, install immediately after writing with limited or no interim
testing. The skill format is low-risk: pure instructions, no
executables, easy to revise in place.

Publishing is equally urgent. If a skill isn't version-controlled in
a known location and available across the user's working environments,
it erodes trust in the entire skills workflow. Skills that feel
chaotically scattered — local copies here, stale versions there, no
change history — discourage the user from investing time in writing
or adopting them. Publish promptly to a tracked, central location so
the user can rely on skills being available, up to date, and backed
up wherever they work.

The exception is publishing to broadly adopted skills marketplaces
where multiple users are affected. There, test thoroughly before
publishing — a broken skill at scale is worse than a delayed one.

### 1. Install locally

Install the skill so it's available in your agent platform before
publishing anywhere.

| Scope | Path | When to use |
|-------|------|-------------|
| User / machine | `~/.claude/skills/<name>/SKILL.md` | Default. Available in all projects on this machine. |
| Project | `.claude/skills/<name>/SKILL.md` | Skill is specific to this repo and should be versioned with it. |
| Gemini | `gemini skills install <path-or-url>` | Gemini CLI native install. |

**User-scope is the default.** Install at project scope only when the
skill is inherently tied to the repo (e.g., repo-specific workflow,
project conventions).

**Project-scoped skills and git tracking.** When installing at project
scope, ensure the skill files will be version-controlled:

1. Check that `.claude/skills/` is not gitignored. Many repos ignore
   `.claude/` entirely — add a `!.claude/skills/` exception in
   `.gitignore` if needed.
2. Run `git status` after creating the skill to confirm the new
   `SKILL.md` appears as untracked or staged.
3. If a `.gitignore` change was required, verify it didn't expose
   other files under `.claude/` (settings, cache, logs). Evaluate any
   newly surfaced files case by case before committing.

The `setup-agent-context` skill, if available, covers `.gitignore`
management for agent directories in detail — including per-file
guidance on what to version vs. exclude.

### 2. Test the skill

**Verify it's discoverable.** Before testing behavior, confirm the
agent platform sees the skill:

```bash
# Gemini CLI
gemini skills list

# Claude Code — check the slash menu or ask:
claude -p "list your available skills"
```

If the skill doesn't appear, check the install path and directory name.

**Test behavior.** Run a headless prompt that indirectly reveals
whether the skill loaded and influenced the agent's behavior. The
prompt should exercise the skill's guidance without requiring actual
disk I/O or other privileged tool usage — this keeps the test fast
and safe.

```bash
# Claude Code
claude -p "prompt that reveals the skill's effectiveness"

# Gemini CLI
gemini -p "prompt that reveals the skill's effectiveness"
```

**Designing a good test prompt:**

- Ask the agent to describe how it would approach a task the skill
  covers. The response should reflect the skill's specific guidance,
  not generic behavior.
- If the skill has distinctive rules or preferences, ask about a
  scenario where those rules apply and check whether the response
  follows them.
- Add `--allowedTools ""` or similar flags to prevent actual tool
  execution if the prompt might trigger it. The goal is to verify the
  skill shaped the agent's reasoning, not to run a full workflow.
- For skills with `user-invocable: true`, test slash-command invocation
  too: does `/my-skill` trigger it?

### 3. Publish

Once the skill works locally, publish it. Skills that stay local get
forgotten — publish promptly so the skill is available where you (and
others) will actually use it. If the user hasn't specified a
destination, ask where it should go and push for a decision now.

#### Where to publish

**Cross-platform skills** go in the primary skills marketplace (e.g.,
echoskill). These work across agents and belong in topical collections
(`coding/`, `prompting/`, `consulting/`).

**Platform-specific skills** go in a platform-specific collection or repo.
If a skill genuinely only works on one agent (e.g., depends on Claude Code's
`context: fork` or Gemini-specific features), publish it under a
platform-specific collection (e.g., `claude/`) in the marketplace, or in a
platform-specific repo. Don't pollute the primary cross-platform marketplace
with skills that only work on one agent.

### Determine placement

Glob the target repo for `*/SKILL.md` and `*/*/SKILL.md` to understand how
skills are organized. Show the user the existing structure and confirm which
collection the skill belongs in. If the skill already exists (same name),
confirm the user wants to update it.

### Validate before publishing

Before copying to the target:

- **Frontmatter is complete**: `name` and `description` are required.
- **Name matches directory name.**
- **No references to specific consuming repos or projects.** Usage
  examples must be generic. If repo-specific references are found,
  rewrite them to be generic before publishing.
- **No bundled scripts** unless the skill is part of a plugin.
- **No hard dependencies on non-ubiquitous tools** without offering
  alternatives.

### Publish workflow

1. Copy the skill directory to the target repo at the confirmed path
2. Update the README.md table for the collection if one exists
3. `git diff --staged` to review
4. Confirm with the user
5. Commit and push

### Installing from a marketplace on other machines

After publishing, show the user how to install the skill elsewhere.
Use actual values from the publish (repo URL, collection, skill name)
— not angle-bracket placeholders.

**Match existing patterns first.** Before choosing an install method,
check how other skills from the same marketplace/repo are already
installed on this machine. Look at `~/.claude/skills/` — are existing
skills symlinked, copied, or plugin-managed? Check `gemini skills list`
— are they installed or linked? Follow the established pattern rather
than introducing a new one. Save the install method to memory if not
already saved, so future publishes are consistent without re-discovery.

**Gemini CLI:**

```bash
# Install a single skill from a collection
gemini skills install <repo-url> --path <collection>/<skill-name>

# Install an entire collection
gemini skills install <repo-url> --path <collection>

# Link a local clone (live updates, no reinstall needed)
gemini skills link <local-path>/<collection>/<skill-name>
```

`gemini skills link` creates a live link — edits to the source are
reflected immediately with no reinstall. Prefer this over `install`
when working from a local clone of the skills repo.

**Claude Code:**

Claude Code has no skill management CLI. Install by symlinking from
a local clone of the marketplace repo:

```bash
# Clone the skills repo (once per machine)
git clone <repo-url> <local-path>

# Symlink the skill
ln -s <local-path>/<collection>/<skill-name>/SKILL.md \
  ~/.claude/skills/<skill-name>/SKILL.md
```

Symlinks keep the local install in sync with `git pull` — no re-copy
needed after updates.

**Plugin-bundled skills:**

If the skill ships inside a Claude Code plugin rather than a
standalone marketplace, the install command is different:

```bash
claude plugin install <plugin-name>@<marketplace> --scope user
```

Skills bundled in plugins are managed by the plugin lifecycle, not
by manual symlinks or copies.

### Reconcile local installs with skills repo

Skills drift when they exist in multiple places — the local platform
install directory and the personal skills repo. Every publish action
is an opportunity to reconcile.

**Locate the skills repo.** Check memory for a previously saved
skills repo path. If not found, ask the user where their personal
skills repo / marketplace lives and save it to memory for future
sessions (e.g., memory name: `skills-repo-location`, type:
`reference`).

**Known local install locations:**
- `~/.claude/skills/<name>/SKILL.md` — Claude Code user-scope
- `~/.gemini/skills/<name>/SKILL.md` — Gemini CLI user-scope (if
  applicable; check `gemini skills list` for installed locations)
- `.claude/skills/<name>/SKILL.md` — project-scope (current repo)

**For each skill being published, compare across all locations:**

1. **Gather facts.** For each copy of the skill (local installs +
   repo), check:
   - Does the file exist?
   - File size and last-modified timestamp (`stat` or `ls -la`)
   - Content (`diff` between copies)

2. **Report to the user.** Present a clear status for each location:
   - **Missing in repo but installed locally** — the skill hasn't
     been published yet. Recommend copying local → repo.
   - **In repo but not installed locally** — the skill was published
     but never installed on this machine, or was removed. Recommend
     copying repo → local.
   - **Identical in both** — in sync, nothing to do.
   - **Different** — show the diff. Recommend a direction based on
     timestamps (newer usually wins), but always ask the user which
     version to keep, or whether to merge changes manually.

3. **Act with user's blessing.** After the user confirms the
   direction:
   - Copy the chosen version to the target location(s)
   - Stage, commit, and push the skills repo if it was updated
   - Confirm the local install is current if that was updated

4. **Save the repo location to memory** if not already saved, so
   future publish actions skip the "where is your skills repo?" step.

**Do this reconciliation proactively** — don't wait for the user to
ask. Every time a skill is published or updated, check the other
locations and flag drift. The goal is a single source of truth in the
repo with local installs as consistent copies.

### Consider agent preloading

If the skill was developed for use by a specific agent (e.g., a coding
agent, a review agent), consider whether that agent's `skills:` frontmatter
should be updated to preload it. Preloading injects the full skill content
into the agent's context at startup — the agent doesn't need to discover
or invoke the skill; it just has the knowledge.

```yaml
# In the agent's .md frontmatter:
skills:
  - safe-commit
  - show-code       # ← new skill preloaded here
```

**Platform support for skill preloading in agents:**

- **Claude Code** — supported via `skills:` list in agent/subagent
  frontmatter. Full skill content is injected at startup. Subagents
  don't inherit skills from the parent; list them explicitly.
  ([Claude Code docs: Preload skills into subagents](https://code.claude.com/docs/en/sub-agents#preload-skills-into-subagents))
- **Gemini CLI** — no equivalent mechanism as of 2026. Skills are
  discovered and loaded via progressive disclosure, not preloaded
  into agent definitions.
- **agentskills.io** — the spec covers skill format only, not agent
  definitions or skill-to-agent binding.

**When to preload vs. let the agent discover:**

- Preload when the agent should *always* have this knowledge (e.g.,
  commit workflow, code style rules)
- Let discovery handle it when the skill is situational (e.g.,
  PDF processing, dependency evaluation)

## Cross-Skill References

Skills must be self-contained. A skill that fails or misleads when a
referenced skill is absent is a broken skill. Follow these rules when
one skill relates to another:

### Only reference co-packaged skills

Only reference skills distributed in the same unit — same marketplace
collection, same plugin, same repo. Never reference skills from
external sources; they may not be installed.

### Hint-level only

References must be non-essential hints to supplementary content. The
referencing skill must function fully on its own. Use language like:

> "The `setup-agent-context` skill, if available, covers this in
> more detail."

> "See the `safe-commit` skill if installed for commit workflow
> guidance."

Never write references that create a dependency:

> "Follow the steps in `setup-agent-context` to complete this task."

> "This skill requires `safe-commit` to be installed."

### Prefer duplication over cross-skill dependencies

If a skill needs specific content from another skill to work correctly,
duplicate that content inline. Three repeated paragraphs are better
than a dependency chain that breaks when a skill is missing.

### Exception: platform-native bundled skills

Skills that are privately co-bundled into an **agent platform** (Claude
Code, Gemini CLI, Cursor, or similar native agent environments) — and
are NOT also published from the same source into a skills marketplace —
may use firm cross-references. The platform ships them as a unit, so
co-presence is guaranteed.

This exception does NOT apply to marketplace-published skills, even if
they also happen to be bundled into a platform. If a skill is available
outside the platform (via a marketplace, a shared repo, or standalone
installation), it must follow the hint-level rules above, because
marketplace consumers may pick and choose which skills to install.

### Terminology note

**Agent platform** is the umbrella term for native agent environments
— Claude Code, Gemini CLI, Cursor, and similar tools where agents
execute with access to tools, files, and skills. Use "agent platform"
(not "IDE", "CLI", or "runtime" alone) when referring to this category
generically.
