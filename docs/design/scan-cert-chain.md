# Scan Certification Chain Design

## Problem

There's a gap between when privacy-guard scans and when the user pushes.
Content can change (amend, rebase, new commit) between scan and push,
and the push goes through unchecked. A rogue parent agent could also
skip the scan entirely or tell the subagent to fake clean results.

## Threat model

1. **Sloppy user** — forgets to scan, doesn't want to disable hooks
2. **Rogue parent agent** — skips scan or tells subagent to fake results
3. **NOT:** sophisticated attacker with machine access (they control everything)

## Design: SHA-anchored certification via hooks

### The anchor: HEAD SHA

Git commit SHAs hash everything: file content, commit message, author
name, author email, timestamps, and parent SHA. If any prior commit in
the chain changes, all descendant SHAs change. HEAD SHA is a single
value that represents the entire state of what would be pushed.

### Flow

```
1. User commits work (may be multiple commits)
2. Something triggers privacy-guard subagent scan
3. SubagentStop hook fires:
   a. Reads agent_transcript_path JSONL
   b. Verifies prompt wasn't tampered ("skip scan", etc.)
   c. Verifies agent actually made tool calls (not a faked fast response)
   d. Reads last_assistant_message for scan result
   e. Computes sha = git rev-parse HEAD
   f. Writes cert: ~/.cache/claude-coding-plugin/HEAD-<sha>.passed
4. User pushes:
   a. sha = git rev-parse HEAD (or user-specified ref)
   b. Check cert exists for that sha
   c. git push origin $sha:refs/heads/<branch>
```

### Why HEAD SHA is sufficient

- Amend a commit → HEAD changes → old cert invalid
- Add a new commit → HEAD changes → old cert invalid
- Rebase → HEAD changes → old cert invalid
- Edit commit message → HEAD changes → old cert invalid
- Change author name/email → HEAD changes → old cert invalid
- Change any ancestor commit → cascades to HEAD → old cert invalid

### Branch doesn't matter

The cert says "this SHA's content is clean." The PII question is about
content, not destination. What branch the user is on or pushes to is
irrelevant to whether the content contains PII.

- User on `feature/foo`, scan passes, cert for SHA aaa
- User switches to `main` → HEAD is now SHA bbb → no cert → blocked
- User switches back to `feature/foo` → HEAD is SHA aaa → cert exists → allowed

No branch-level tracking needed.

### TOCTOU protection

Capture SHA once, check cert, push that exact SHA:

```bash
sha=$(git rev-parse HEAD)
# verify cert exists for $sha
git push origin $sha:refs/heads/$(git symbolic-ref --short HEAD)
```

If someone amends between check and push, doesn't matter — pushing the
certified SHA, not whatever HEAD moved to.

## Q&A from design session

### Can the parent agent forge a cert?

No. The cert is written by a SubagentStop hook — a shell script that
runs outside any agent's context. The parent doesn't control when it
fires or what it writes.

### Can the parent send "skip scan" to the subagent?

The SubagentStop hook reads `agent_transcript_path` (the subagent's
full JSONL). It verifies:
- The prompt wasn't tampered (no "skip", "fake", "report clean")
- The agent actually made tool calls (git diff, etc.)
- A fast-faked response with no tool calls gets rejected

### Can the parent race two subagent calls?

In theory: send a real scan and a fake "skip scan" simultaneously.
The fake returns first, SubagentStop writes the cert.

Defense: the hook verifies the transcript has real tool calls. A
"skip scan" subagent has zero tool calls → hook rejects it. Only a
subagent that actually ran git commands gets a cert written.

### Does SHA change with different commit message or author?

Yes. The SHA hashes: tree (files), parent(s), author name + email +
timestamp, committer name + email + timestamp, commit message. Change
any → different SHA.

### What if a prior commit changes?

Each commit's SHA includes its parent SHA. Change commit #3 in a chain
of 5 → #3 gets new SHA → #4's parent changes → #4 gets new SHA → ...
→ HEAD gets new SHA. Any change anywhere cascades to HEAD.

### Can they cheat by switching branches?

No. Switching branches changes HEAD to a different SHA. The cert for
the old SHA doesn't apply. If they switch to a branch that has a cert,
that means it was scanned — which is fine.

### What about `push_scanned(sha)` from wrong branch?

Content at that SHA was certified. Where it lands on remote doesn't
introduce PII. Git may reject as non-fast-forward anyway.

### What about specifying a ref (branch/tag)?

`git rev-parse <anything>` resolves to SHA. The tool resolves, checks
cert, pushes the SHA. Branch name and tag name are just pointers to
SHAs.

### What if they manually create the cert file?

Add a seed from `~/.config/ai-common/privacy-guard-seed` (a file
no agent reads). Cert content: `hash(seed + sha)`. Pre-push hook
reads same seed, recomputes, verifies. User would need to know the
seed to forge it. This is optional hardening — for the sloppy-user
threat, file existence is probably enough.

### Is there a writable cache dir for agents?

No. Claude Code exposes `CLAUDECODE=1` and `CLAUDE_CODE_ENTRYPOINT`
but no cache/data dir. Hooks are shell scripts and can write anywhere.
The cert is written by the hook, not the agent.

### Can we correlate scan request to scan response?

Via the transcript at `agent_transcript_path`. The SubagentStop hook
reads the JSONL, which contains both the initial prompt (request) and
all tool calls + final response. Single source of truth.

### How many user prompts in a subagent transcript?

Expected: exactly one. The parent sends one prompt, the subagent works
until done. No interactive back-and-forth. `maxTurns` controls how
many tool-call turns the subagent takes, not user messages. This
should be verified empirically (workbench test).

## Implementation components

### Plugin side (claude-coding-plugin)

1. **SubagentStop hook** (`hooks/hooks.json`)
   - Matcher: `privacy-guard`
   - Script reads transcript, validates, writes cert

2. **`push_scanned` MCP tool or skill**
   - Resolves ref to SHA
   - Checks cert
   - Pushes `$sha:refs/heads/<branch>`

3. **Cert storage**
   - Location: `~/.cache/claude-coding-plugin/`
   - Filename: `scan-<sha>.cert`
   - Content: `hash(seed + sha)` or just presence check

### Push blocking (PreToolUse on Bash)

A `PreToolUse` hook matching `Bash(git push*)` checks the cert before
allowing any push. This blocks the agent from pushing uncertified
content. The hook script reads `tool_input.command` from JSON stdin
and validates with regex — the glob matcher is just the entry point,
the script does the real check. This handles edge cases like extra
whitespace or unusual argument ordering that glob matching might miss.

All known push vectors and their matchers:

| Vector | Matcher | Risk |
|--------|---------|------|
| `git push` | `Bash(git push*)` | Primary — most common |
| `gh pr create` | `Bash(gh pr*)` | Implicit push of branch |
| `gh api` | `Bash(gh api*)` | Direct API POST to refs |
| `curl` to GitHub API | `Bash(curl*)` | Raw HTTP push |
| `wget` to GitHub API | `Bash(wget*)` | Raw HTTP push |
| `python3 -c "..."` | `Bash(python*)` | subprocess.run(['git','push']) |
| `node -e "..."` | `Bash(node*)` | child_process.exec('git push') |
| `bash -c "git push"` | `Bash(bash*)` | Nested shell |
| `sh script.sh` | `Bash(sh *)` | Script contains push |
| Write a script then execute | `Bash` (broad) | Indirect — hard to catch |

**For this plugin: block `git push` only.** The hook output tells
the agent and user there's a problem — no clean scan. That's the
guardrail for sloppy users and rogue parent agents. We're not trying
to stop someone who's logged in and determined to corrupt the repo.

The other vectors (curl, gh api, python subprocess, etc.) are
documented above for awareness. A future hook script matching `Bash`
broadly with regex validation of `tool_input.command` could cover
them, but the latency tradeoff (hook fires on every Bash call) isn't
worth it for the current threat model.

**The next level of defense is separate from this plugin.** A GitHub
Actions workflow that scans PRs via the CI/CD pipeline (issue #6)
would require all pushes to go through PRs, and the PR gets scanned
by an independent agent in CI. That's a different product — it
catches everything regardless of what the local agent or user did.
The local plugin is the fast feedback loop; the CI scan is the
enforcement gate. They're complementary layers, not redundant.

For pushes outside Claude (user terminal), a git pre-push hook
provides the same check as a belt-and-suspenders layer.

### Workbench tests (claude-workbench)

1. **SubagentStop receives last_assistant_message** — proves hook gets output
2. **SubagentStop receives agent_transcript_path** — proves we can read transcript
3. **Transcript has exactly one user prompt** — proves no injection
4. **Transcript has tool calls** — proves real scan happened
5. **PreToolUse on Agent sees prompt** — optional, proves we can inspect/block
6. **PreToolUse on Bash catches push variants** — test `git push`, `git  push`, `git push --force`, etc.
7. **Glob matcher edge cases** — leading spaces, internal spaces, chained commands

## Related issues

- echomodel/claude-coding-plugin#8 — Dual-context agent execution
- echomodel/claude-coding-plugin#6 — CI/CD integration
- echomodel/claude-coding-plugin#7 — Modular agent composition

## Session

- Name: `privacy-guard-lean-rewrite` (branched to `claude-session-archiving-for-ccx`)
- Date: 2026-04-06
