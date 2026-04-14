---
name: setup-agent-context
description: "Configure coding agent context for a repo by setting up CLAUDE.md, .gemini/settings.json, and .gitignore rules. Use when starting a new project, onboarding a repo for AI-assisted development, or when asked to set up agent context, configure Claude/Gemini for a repo, or make a repo AI-ready."
---

Set up the standard agent context files so that Claude Code and Gemini CLI
both automatically load the repo's README.md and CONTRIBUTING.md as context.

## What this skill creates/updates

1. **`CLAUDE.md`** (repo root) — a short pointer file
2. **`.gemini/settings.json`** (repo root) — context file declarations
3. **`.gitignore`** — exclude `.gemini/` but include `!.gemini/settings.json`
4. **`README.md` / `CONTRIBUTING.md`** — links to every `docs/**/*.md`

## What belongs where

CLAUDE.md tells agents where to look. The actual content lives in:

- **README.md** — what the project is, how to install and use it
- **CONTRIBUTING.md** — architecture, design principles, constraints, testing
  conventions, SDK structure, how to add features

This separation means both Claude Code and Gemini CLI get identical context
from the same source files, with no duplication. Every other placement rule
in this skill — including which file should link which docs — derives from
this split.

## Step 1: Read existing files

Before making changes, read these files if they exist:
- `CLAUDE.md`
- `.gemini/settings.json`
- `.gitignore`
- `README.md` (to confirm it exists)
- `CONTRIBUTING.md` (to confirm it exists)

If README.md or CONTRIBUTING.md don't exist, tell the user and ask whether
to proceed anyway or create them first.

## Step 2: Ensure every `docs/**/*.md` is linked from README.md or CONTRIBUTING.md

Any markdown file living under `docs/` is only useful if readers (human or
agent) can discover it. The root `README.md` (and, for contributor-facing
docs, `CONTRIBUTING.md`) must link to every such file.

### Rules

- **Every `docs/**/*.md` file must be reachable** from `README.md` or
  `CONTRIBUTING.md`. Transitive discovery via an intermediate doc is fine
  (e.g., `README.md` → `docs/index.md` → `docs/third-party-product/categories.md`) as
  long as the chain starts at a top-level document.
- **Links must use markdown hypertext syntax** with both a descriptive
  title and a relative URL — e.g.,
  `[Third-Party Product Categories](docs/third-party-product/categories.md)`. Bare URLs,
  paths without titles, or plain text filenames are not sufficient.
- **Link titles must read as natural prose**, not filenames. No `.md`
  extension, no directory segments, no snake_case / kebab-case, no
  `UPPERCASE_IDS`. The title is what a human reader sees — it should be
  a short descriptive phrase (title case or sentence case), not the
  technical identifier of the target file.
  - Good: `[Third-Party Product Categories](docs/third-party-product/categories.md)`
  - Bad: `[docs/third-party-product/categories.md](docs/third-party-product/categories.md)`
  - Bad: `[categories.md](docs/third-party-product/categories.md)`
  - Bad: `[third-party-product-categories](docs/third-party-product/categories.md)`
  - This rule applies to every link between docs — README → docs, docs →
    docs, CONTRIBUTING → docs. Fix existing offenders when encountered.
- **Relative URLs only.** Never absolute paths or
  `https://github.com/.../blob/...` links for intra-repo docs — relative
  links stay correct across forks, mirrors, and local checkouts.
- **Audience determines which file links the doc.** Apply the README vs
  CONTRIBUTING split defined in "What belongs where" above:
  user-facing docs are linked from README.md; contributor-facing docs are
  linked from CONTRIBUTING.md. When a doc is genuinely dual-audience,
  prefer README.md and cross-link from CONTRIBUTING.md if helpful.
- **Every link carries a short summary of what it points to.** Never leave
  a bare link that a reader (or agent) has to open blindly. Pair each link
  with a 1-2 sentence description of the target doc's content — enough
  that someone who doesn't open the link still has a working mental model
  of what's there. This applies in both directions: from README or
  CONTRIBUTING down to docs, and from one doc to another.

  Two reasons:

  1. **Context residency.** Agents and humans often read the referring
     doc without following every link. A short summary ensures at least
     a skeletal understanding of the linked content is in memory even
     when the target isn't fetched. Bare links add zero context.
  2. **Informed incentive to open the target.** A title alone doesn't
     tell a reader whether the linked doc is worth loading right now.
     A summary lets them decide whether the target is relevant to their
     current task.

  Example shapes:

  - **Prose with inline link:** "See [Third-Party Product Categories](docs/third-party-product/categories.md),
    which lists every default category, its group, and the group's
    income/expense/transfer type, and explains why the product's defaults
    can double-count certain flows if left unchanged."
  - **Sectioned list with description:** a heading like "Documentation"
    followed by bullets where each bullet is `[Title](path)` — 1-2
    sentence summary. More compact than prose when linking many docs
    at once.

  Keep summaries short (one to two sentences). If a doc needs a longer
  description, that's a signal the title itself should be more
  descriptive, or the target should have a clearer lead paragraph that
  can be mirrored.

### Process

1. Enumerate all `docs/**/*.md` files.
2. For each one, search `README.md` and `CONTRIBUTING.md` for a markdown
   link to that relative path. A match anywhere in the chain of linked docs
   counts (transitive is fine).
3. For any unlinked doc, tell the user which file was found and propose a
   placement (README.md vs CONTRIBUTING.md, and which section or heading).
4. After user confirmation, add the links using descriptive titles and
   relative URLs. Group related docs under a section heading like
   "Documentation", "References", "Architecture", etc. — don't sprinkle
   orphan bullets at the bottom.

If the repo has no `docs/` directory, skip this step.

## Step 3: Create or update CLAUDE.md

The file should use Claude Code's `@path` import syntax to pull README.md
and CONTRIBUTING.md into context at session start. Do not put project-specific
instructions here — those belong in CONTRIBUTING.md. The CLAUDE.md content
should be:

```markdown
@README.md
@CONTRIBUTING.md
```

If additional lines already exist in CLAUDE.md (e.g., PII warnings for
public repos), preserve them. Only add the `@` imports if missing.

## Step 4: Create or update .gemini/settings.json

```json
{
  "context": {
    "fileName": [
      "README.md",
      "CONTRIBUTING.md"
    ]
  }
}
```

If the file already exists, merge the context entries — don't overwrite
other settings that may be present.

## Step 5: Update .gitignore

Agent context directories (`.claude/`, `.gemini/`) contain a mix of
versioned configuration and local-only state. The `.gitignore` must
selectively include the files that should be shared while excluding
everything else.

Ensure these entries exist in `.gitignore`:

```
.claude/
!.claude/skills/
.gemini/
!.gemini/settings.json
```

**Why each line matters:**
- `.claude/` — excludes local Claude Code state (settings, cache, MCP config)
- `!.claude/skills/` — re-includes project-scoped skills so they're versioned
- `.gemini/` — excludes local Gemini state files
- `!.gemini/settings.json` — re-includes context configuration

Only add the `.claude/skills/` exception if the project actually has or
will have project-scoped skills. Don't pre-create it speculatively.

## Step 6: Verify git tracking

After modifying `.gitignore` or adding context/settings files for the
first time, run `git status` and verify:

1. **Expected files appear.** New or modified files under `.claude/` or
   `.gemini/` should show as untracked or staged — not invisible. If a
   file you just created doesn't appear in `git status`, the `.gitignore`
   is still excluding it. Debug the ignore rules.

2. **No unexpected files surfaced.** Changing `.gitignore` exclusion
   patterns can expose files that were previously hidden. If ANY file
   under `.claude/` or `.gemini/` newly appears in `git status` as a
   result of a `.gitignore` change, evaluate it **case by case** before
   proceeding. Do not batch-add or assume safety. Specific guidance:

   - **`.claude/settings.json` and `.gemini/settings.json`** — version
     these when they contain clean, portable, agent-helpful config:
     `context.fileName` arrays, `allowedTools` lists, tool permissions,
     or other settings that help collaborators and agents work
     consistently. These are valuable to share. But read the full file
     first — verify it contains no absolute paths with usernames,
     credentials, API keys, or references to local-only MCP servers
     by path. If clean: stage and commit. If not: clean it up or add
     a specific ignore rule.
   - **Cache, log, or state files** (e.g., `.cache/`, `*.log`,
     session history, MCP connection state) — never version these.
     They are ephemeral, machine-specific, and add noise. Add specific
     ignore rules if they surface.
   - **Any other file** under these directories that newly surfaces —
     do not commit without reading its content and understanding why it
     exists. When in doubt, add a specific ignore rule for it.

3. **Confirm with `git check-ignore`.** For any file you expect to be
   tracked, run `git check-ignore -v <path>` to confirm it is NOT
   ignored. For files that should stay excluded, confirm they ARE ignored.

## Step 7: Security scan before committing

Before staging any file under `.claude/` or `.gemini/` for commit, scan
its content for sensitive data:

- **Absolute paths with usernames** — `/Users/<name>/`, `/home/<name>/`.
  Replace with `~`, `$HOME`, or relative paths.
- **API keys, tokens, credentials** — never commit these, even to
  private repos.
- **User-specific identifiers** — GCP project IDs, Google Doc IDs, email
  addresses, account IDs.
- **Local MCP server registrations** — `.claude/settings.json` often
  contains `stdio` server entries with absolute paths to local
  executables. These are not portable and should not be committed.
- **Allowed-tool lists** — `.gemini/settings.json` may contain
  `allowedTools` arrays. These are generally safe to commit (they help
  collaborators), but verify they don't reference local-only MCP servers
  by path.

**The rule:** if a `.json` file under `.claude/` or `.gemini/` is being
git-added for the first time or has changed after a `.gitignore` edit,
read its full content and verify it contains nothing user-specific or
sensitive before committing. This is especially important because these
files are easy to commit reflexively with `git add .` without reviewing.

## Step 8: Report

Tell the user what was created or updated. Mention that both Claude Code
and Gemini CLI will now load README.md and CONTRIBUTING.md as context, and
that project-specific instructions belong in CONTRIBUTING.md. If any
`docs/**/*.md` files were newly linked, list them and note where the link
was added. If `.gitignore` was modified, note which files are now versioned
and confirm no sensitive content was exposed.
