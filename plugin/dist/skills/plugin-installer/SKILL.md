---
name: plugin-installer
description: >-
  Install, update, or reinstall a Claude Code plugin from a marketplace.
  Use when the user says "install plugin", "update plugin", "reinstall
  plugin", "bump plugin version", "release plugin", "publish plugin",
  or when a plugin needs to pick up source code changes from its repo.
  Covers first-time install, version bumps, marketplace ref updates,
  and cache refresh.
---

# Install or Update a Claude Code Plugin

Handles first-time plugin installation from a marketplace and
reinstallation after source code changes. The workflow is the same
either way — the only difference is whether the marketplace entry
already exists.

## Step 1: Identify the plugin

Find the plugin's `.claude-plugin/plugin.json`. Glob for it:

```
**/. claude-plugin/plugin.json
```

If multiple are found, prefer the one whose parent directory is
colocated with a `Makefile` — that indicates a build-based plugin
where the `plugin.json` is the source of truth, not a dist copy.

If only one exists, use it directly.

Read the `plugin.json` to get the current `name` and `version`.

## Step 2: Build (if applicable)

Check whether a `Makefile` with a `build` target exists in the same
directory as (or a parent of) the `.claude-plugin/` directory.

**If a Makefile with a `build` target exists:**

If the user wants a version bump, pass the new version:
```bash
make -C <makefile-dir> build VERSION=X.Y.Z
```

Otherwise build without a version:
```bash
make -C <makefile-dir> build
```

If the build fails (non-zero exit), stop and report the error.

**If no Makefile or no `build` target:** skip this step. The plugin
directory is assumed ready to go as-is.

## Step 3: Bump version (if no build handled it)

If no build step ran but the user wants a version bump, edit the
`plugin.json` directly — increment the `version` field.

If a build step ran with `VERSION=`, the build already handled this.

## Step 4: Commit and tag

Stage all changed files (source, dist, version):

```bash
git add -A
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

**Do not push yet.** Show the user the commit and give them the push
command. Wait for confirmation — this is their opportunity to review
or scan the commit before it goes to the remote.

```bash
git push origin main --tags
```

## Step 5: Update marketplace ref

After the push, find the marketplace repo. Check memory for a saved
marketplace path. If not found, run `claude plugin list` to see the
marketplace name, then check for a local clone. Ask the user if
needed, and save the path to memory.

Edit the marketplace's `marketplace.json`:
- If the plugin entry exists, update the `ref` field to the new tag
  (e.g., `"ref": "vX.Y.Z"`)
- If this is a first-time install, add a new entry with the plugin's
  name, source URL, path (if git-subdir), and ref

Commit and push the marketplace repo.

## Step 6: Install or update the plugin

```bash
claude plugin marketplace update <marketplace-name>
claude plugin update <plugin-name>@<marketplace-name> --scope user
```

If `update` reports "already at latest version" or the plugin isn't
installed yet, use `install`:

```bash
claude plugin install <plugin-name>@<marketplace-name> --scope user
```

## Step 7: Verify and report

Check the installed version:

```bash
claude plugin list
```

Confirm the version matches. Tell the user to restart Claude Code —
plugin changes (especially MCP servers and hooks) take effect on
session start, not mid-session.

## Troubleshooting

- **Marketplace still serves old version**: verify the git tag exists
  on the remote (`git ls-remote --tags origin | grep vX.Y.Z`) and
  that `marketplace.json` has the correct ref.
- **`plugin update` says already current**: the marketplace cache may
  be stale. Run `claude plugin marketplace update` first. If still
  stuck, uninstall and reinstall.
- **Installed plugin is missing recent changes**: run `git status` and
  `git log @{u}..HEAD` in the plugin repo. If there are uncommitted
  or unpushed changes, the tagged version doesn't include them.
  Commit, push, bump again — never retag an existing version.
- **MCP tools not appearing**: start a new Claude Code session. MCP
  servers connect at session start and don't hot-reload.
