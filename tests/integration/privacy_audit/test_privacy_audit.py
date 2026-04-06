"""Integration tests for the privacy-audit agent.

Run explicitly:  pytest tests/integration/privacy_audit/ -v
Skip slow tests: pytest tests/integration/privacy_audit/ -v -m "not slow"

Each test creates isolated temp repos and a fictitious PERSON.md,
invokes the agent via CLI, and parses the structured JSON output.
"""

import os

import pytest

from .conftest import (
    FAKE_PERSON,
    _add_and_commit,
    _e,
    _init_git_repo,
    _write_person_md,
    run_privacy_guard,
)


# -----------------------------------------------------------------------
# Configuration & startup failures
# -----------------------------------------------------------------------

class TestStartupFailures:
    """Agent should fail fast and report structured errors."""

    def test_missing_person_md(self, clean_repo):
        """Agent exits with failure when PERSON.md is not found."""
        bogus_path = clean_repo.parent / "nonexistent" / "PERSON.md"
        result = run_privacy_guard(clean_repo, person_md_path=bogus_path)

        assert result["status"] == "failed"
        assert result.get("failure_reason") is not None
        assert "person" in result.get("failure_reason", "").lower() or \
               "pattern" in result.get("summary", "").lower()
        assert result["findings"] == []

    def test_unconfigured_categories_warning(self, test_root, clean_repo):
        """Agent warns when PERSON.md has empty/commented categories."""
        sparse_md = test_root / "person_md" / "PERSON.md"
        sparse_md.write_text(
            "# Sparse\n"
            "---\n"
            "patterns:\n"
            "  names:\n"
            "    - Zanzibar\n"
            "  # cloud_ids: []\n"
            "  # financial_providers: []\n"
            "---\n"
        )
        result = run_privacy_guard(clean_repo, person_md_path=sparse_md)

        assert result["status"] in ("completed", "partial")
        # Should report unconfigured categories somewhere
        unconfigured = result.get("unconfigured_categories", [])
        warnings = result.get("warnings", [])
        combined = str(unconfigured) + str(warnings)
        assert "cloud_ids" in combined.lower() or "not configured" in combined.lower() or \
               len(unconfigured) > 0


# -----------------------------------------------------------------------
# Pattern detection from PERSON.md
# -----------------------------------------------------------------------

class TestPatternDetection:
    """Agent finds PII that matches PERSON.md patterns."""

    def test_email_in_file(self, person_md, dirty_repo):
        """Finds a PERSON.md email address in a committed file."""
        result = run_privacy_guard(dirty_repo, person_md_path=person_md)

        assert result["status"] == "completed"
        email_findings = [f for f in result["findings"]
                          if f.get("category") == "emails"
                          or _e("zanzibar", "quux.example") in f.get("matched_value", "")]
        assert len(email_findings) > 0

    def test_name_in_file(self, person_md, dirty_repo):
        """Finds a PERSON.md name in committed file content."""
        result = run_privacy_guard(dirty_repo, person_md_path=person_md)

        name_findings = [f for f in result["findings"]
                         if "Plonkia" in f.get("matched_value", "")
                         or "Frobnitz" in f.get("matched_value", "")]
        assert len(name_findings) > 0

    def test_financial_provider_in_file(self, person_md, dirty_repo):
        """Finds a PERSON.md financial provider in file content."""
        result = run_privacy_guard(dirty_repo, person_md_path=person_md)

        fin_findings = [f for f in result["findings"]
                        if "Xyzzy Bank" in f.get("matched_value", "")]
        assert len(fin_findings) > 0

    def test_property_name_in_file(self, person_md, dirty_repo):
        """Finds a PERSON.md property name in file content."""
        result = run_privacy_guard(dirty_repo, person_md_path=person_md)

        prop_findings = [f for f in result["findings"]
                         if "Frobnitz Manor" in f.get("matched_value", "")]
        assert len(prop_findings) > 0

    def test_clean_repo_no_findings(self, person_md, clean_repo):
        """Clean repo produces zero findings."""
        result = run_privacy_guard(clean_repo, person_md_path=person_md)

        assert result["status"] == "completed"
        assert len(result["findings"]) == 0


# -----------------------------------------------------------------------
# Location-specific detection
# -----------------------------------------------------------------------

class TestLocationDetection:
    """Agent finds PII in various git locations, not just HEAD files."""

    def test_history_not_scanned_by_default(self, person_md, dirty_repo):
        """Default scan does NOT find PII that was removed from HEAD.

        dirty_repo has a test email in commit 1's config.yaml
        but it was replaced in commit 2. A default scan should NOT find
        the email in config.yaml since it's no longer at HEAD.
        """
        result = run_privacy_guard(dirty_repo, person_md_path=person_md)

        assert result["status"] == "completed"
        # The email should NOT appear from config.yaml (only from docs/contact.md)
        config_yaml_findings = [f for f in result["findings"]
                                if "config.yaml" in f.get("location", "")]
        assert len(config_yaml_findings) == 0

    def test_pii_in_prior_commit_when_asked(self, person_md, dirty_repo):
        """Finds PII in prior commit WHEN full history is requested.

        Same repo, but this time we ask for full history. The email in
        commit 1's config.yaml should now be found.
        """
        result = run_privacy_guard(
            dirty_repo, person_md_path=person_md,
            extra_prompt="Scan full git history.",
        )

        assert result["status"] in ("completed", "partial")
        # Should find the email in history even though HEAD is clean
        history_findings = [f for f in result["findings"]
                            if _e("zanzibar", "quux.example") in f.get("matched_value", "")
                            and f.get("location_type") in ("commit_message", "file_content", None)
                            or "commit" in f.get("location", "").lower()]
        assert len(history_findings) > 0

    def test_pii_in_commit_message(self, person_md, pii_in_commit_message_repo):
        """Finds PII in commit message text (not file content)."""
        result = run_privacy_guard(pii_in_commit_message_repo, person_md_path=person_md)

        assert result["status"] == "completed"
        msg_findings = [f for f in result["findings"]
                        if f.get("location_type") == "commit_message"
                        or "commit" in f.get("location", "").lower()]
        # Should find Zanzibar and/or Quuxville in the commit message
        matched_values = " ".join(f.get("matched_value", "") for f in msg_findings)
        assert "Zanzibar" in matched_values or "Quuxville" in matched_values



# -----------------------------------------------------------------------
# OS-level detection
# -----------------------------------------------------------------------

class TestOSDetection:
    """Agent discovers OS identifiers at runtime and scans for them."""

    @pytest.mark.env_dependent
    def test_os_username_in_file(self, person_md, test_root):
        """Finds the OS username when planted in a file."""
        username = os.environ.get("USER", os.environ.get("USERNAME", ""))
        if not username or len(username) < 3:
            pytest.skip("OS username too short to test reliably")

        repo = test_root / "repos" / "os-test-repo"
        repo.mkdir(parents=True)
        _init_git_repo(repo)
        _add_and_commit(repo, {
            "config.txt": f"home_dir: /Users/{username}/projects\n",
        }, "add config with path")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] == "completed"
        os_findings = [f for f in result["findings"]
                       if f.get("category") == "os_system"
                       or username in f.get("matched_value", "")]
        assert len(os_findings) > 0


# -----------------------------------------------------------------------
# Judgment / contextual detection
# -----------------------------------------------------------------------

class TestJudgment:
    """Agent uses judgment to flag things not in PERSON.md patterns."""

    def test_unknown_name_in_personal_context(self, person_md, test_root):
        """A name NOT in PERSON.md but used in a clearly personal context
        should ideally be flagged as a contextual finding.

        This tests the agent's judgment. It may not always pass — the
        agent might not flag an unknown name. That's acceptable as long
        as PERSON.md-configured patterns are reliably caught.
        """
        repo = test_root / "repos" / "judgment-repo"
        repo.mkdir(parents=True)
        _init_git_repo(repo)
        _add_and_commit(repo, {
            "README.md": (
                "# My Tool\n\n"
                "Built for tracking Wibblesworth family expenses.\n"
                "Contact: " + _e("wibble", "wobble.example") + "\n"
            ),
        }, "add readme")

        result = run_privacy_guard(repo, person_md_path=person_md)

        # This is a soft assertion — judgment-based detection is best-effort
        contextual = [f for f in result["findings"]
                      if f.get("category") == "contextual"
                      or "judgment" in f.get("note", "").lower()
                      or "personal" in f.get("note", "").lower()
                      or "Wibblesworth" in f.get("matched_value", "")]
        # We don't assert > 0 because this is a judgment call.
        # Instead, just log what happened for manual review.
        if not contextual:
            pytest.xfail("Agent did not flag unknown name — acceptable for judgment-based detection")


# -----------------------------------------------------------------------
# Structured output validation
# -----------------------------------------------------------------------

class TestStructuredOutput:
    """The JSON output block is always present and well-formed."""

    def test_completed_scan_has_required_fields(self, person_md, clean_repo):
        """Successful scan includes all expected top-level keys."""
        result = run_privacy_guard(clean_repo, person_md_path=person_md)

        assert result["status"] == "completed"
        assert "findings" in result
        assert isinstance(result["findings"], list)
        assert "summary" in result or "scan_scope" in result

    def test_failed_scan_has_required_fields(self, clean_repo):
        """Failed scan (missing PERSON.md) still emits structured JSON."""
        bogus = clean_repo.parent / "nope" / "PERSON.md"
        result = run_privacy_guard(clean_repo, person_md_path=bogus)

        assert result["status"] == "failed"
        assert "findings" in result
        assert isinstance(result["findings"], list)
        assert len(result["findings"]) == 0


# -----------------------------------------------------------------------
# Larger repo (slow)
# -----------------------------------------------------------------------

class TestLargerRepo:
    """Tests against a repo with more files and history."""

    @pytest.mark.slow
    def test_larger_repo_exhaustive_scan(self, person_md, test_root):
        """Repo with many files, history, and PII scattered throughout.

        Verifies the agent finds ALL planted items — not just the first
        few. A lazy agent that bails early or samples will fail here.
        """
        repo = test_root / "repos" / "larger-repo"
        repo.mkdir(parents=True)
        _init_git_repo(repo)

        # Create 25 clean files as noise
        clean_files = {}
        for i in range(25):
            clean_files[f"src/module_{i}.py"] = f"# Module {i}\ndef func_{i}(): pass\n"
        _add_and_commit(repo, clean_files, "add modules")

        # Scatter PII across different files, categories, and commits.
        # Each planted value is tracked so we can assert ALL were found.
        expected_findings = {
            _e("zanzibar", "quux.example"): False,    # email, deep in src/
            "Plonkia": False,                  # name, in test fixture
            "Acme Brokerage": False,           # financial, in docs/
            "Quuxville": False,                # city, in config
            "Frobnitz Manor": False,           # property, in a comment
            "Xyzzy Bank": False,               # financial, in a late file
            "Megacorp LLC": False,             # employer, in a mid-repo file
            "synergy bonus": False,            # employer term, in notes
            "zquuxdev": False,                 # github username, in CONTRIBUTING
        }

        # Commit 2: PII in src/ deep in the tree
        _add_and_commit(repo, {
            "src/module_3.py": (
                "# Module 3\n"
                "AUTHOR = '" + _e("zanzibar", "quux.example") + "'\n"
                "def func_3(): pass\n"
            ),
        }, "update module 3")

        # Commit 3: PII in test fixtures
        _add_and_commit(repo, {
            "tests/fixtures/users.json": (
                '[\n'
                '  {"name": "Alice", "role": "admin"},\n'
                '  {"name": "Plonkia", "role": "tester"},\n'
                '  {"name": "Bob", "role": "viewer"}\n'
                ']\n'
            ),
        }, "add test fixtures")

        # Commit 4: PII in docs
        _add_and_commit(repo, {
            "docs/providers.md": "# Providers\n\nWe integrate with Acme Brokerage for portfolio data.\n",
        }, "add provider docs")

        # Commit 5: more clean files as padding
        for i in range(5):
            _add_and_commit(repo, {
                f"src/util_{i}.py": f"# Utility {i}\n",
            }, f"add utility {i}")

        # Commit 6: PII in config and comments — buried after padding
        _add_and_commit(repo, {
            "config/locations.yaml": "regions:\n  - name: Quuxville\n    active: true\n",
            "src/module_18.py": (
                "# Module 18\n"
                "# Check with Frobnitz Manor management about access\n"
                "def func_18(): pass\n"
            ),
        }, "add location config")

        # Commit 7: even more padding
        for i in range(5):
            _add_and_commit(repo, {
                f"lib/helper_{i}.py": f"# Helper {i}\n",
            }, f"add helper {i}")

        # Commit 8: last batch of PII — at the end of history
        _add_and_commit(repo, {
            "src/module_22.py": "# Module 22\nBANK = 'Xyzzy Bank'\n",
            "docs/team.md": "# Team\n\nSponsored by Megacorp LLC.\n",
            "notes/q4.txt": "Q4 goals: synergy bonus target met.\n",
            "CONTRIBUTING.md": "Submit PRs to github.com/zquuxdev/project.\n",
        }, "add remaining docs")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] == "completed"

        # Collect all matched values across findings
        all_matched = " ".join(
            f.get("matched_value", "") + " " + f.get("note", "")
            for f in result["findings"]
        )

        # Assert EVERY planted value was found
        missing = []
        for value in expected_findings:
            if value.lower() not in all_matched.lower():
                missing.append(value)

        assert not missing, (
            f"Agent missed {len(missing)}/{len(expected_findings)} planted findings: {missing}\n"
            f"Total findings reported: {len(result['findings'])}"
        )
