"""Test that privacy-guard agent works when loaded via the plugin.

This test verifies the agent can be discovered and invoked through
the plugin's --plugin-dir mechanism, rather than via a symlink to
.claude/agents/.
"""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from .conftest import (
    _e,
    _init_git_repo,
    _stage_file,
    _write_person_md,
)


PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class TestPluginDiscovery:
    """Agent loads and runs when invoked via --plugin-dir."""

    def test_agent_runs_via_plugin_dir(self, test_root):
        """privacy-guard can be invoked with --plugin-dir pointing at the repo."""
        person_md = test_root / "person_md" / "PERSON.md"
        _write_person_md(person_md)

        repo = test_root / "repos" / "plugin-test-repo"
        repo.mkdir(parents=True)
        # Init WITHOUT symlink — plugin-dir should provide the agent
        env = {**os.environ, "GIT_AUTHOR_NAME": "Test Bot",
               "GIT_AUTHOR_EMAIL": _e("bot", "test.example"),
               "GIT_COMMITTER_NAME": "Test Bot",
               "GIT_COMMITTER_EMAIL": _e("bot", "test.example")}
        subprocess.run(["git", "init", "-b", "main"], cwd=repo,
                       check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Bot"],
                       cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", _e("bot", "test.example")],
                       cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "core.hooksPath", "/dev/null"],
                       cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "initial"],
                       cwd=repo, check=True, capture_output=True, env=env)

        # Stage a file with PII
        _stage_file(repo, "config.yaml",
                    "author: " + _e("zanzibar", "quux.example") + "\n")

        prompt = f"Patterns file at {person_md}. Scan this repo for personal information."
        cmd = [
            "claude",
            "--plugin-dir", str(PLUGIN_ROOT),
            "--agent", "privacy-guard",
            "-p", prompt,
            "--add-dir", str(person_md.parent),
        ]

        debug = os.environ.get("PRIVACY_GUARD_DEBUG")
        if debug:
            log_dir = Path("/tmp/privacy-guard-tests")
            log_dir.mkdir(exist_ok=True)
            cmd.extend(["--debug-file", str(log_dir / "plugin-test.claude-debug.log")])

        result = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True, timeout=180,
        )

        output = result.stdout + result.stderr

        # Extract JSON
        match = re.search(r"```privacy-guard-result\s*\n(.*?)\n```", output, re.DOTALL)
        assert match, f"No JSON block found in output:\n{output[:500]}"

        parsed = json.loads(match.group(1))
        assert parsed["status"] in ("completed", "partial")

        # Should find the staged PII
        email_findings = [f for f in parsed["findings"]
                          if _e("zanzibar", "quux.example") in f.get("matched_value", "")]
        assert len(email_findings) > 0, (
            f"Expected to find staged email via plugin-dir. "
            f"Findings: {parsed['findings']}"
        )
