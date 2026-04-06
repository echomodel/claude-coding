"""Integration tests for the privacy-guard agent (pre-push scanner).

Run explicitly:  pytest tests/integration/privacy_guard/ -v
Skip slow tests: pytest tests/integration/privacy_guard/ -v -m "not slow"

The privacy-guard agent only scans diffs and unpushed commits.
It does NOT read files, scan full history, check issues/PRs, or
verify git author identity.
"""

import pytest

from .conftest import (
    FAKE_PERSON,
    _add_and_commit,
    _e,
    _init_git_repo,
    _stage_file,
    _modify_tracked_file,
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


# -----------------------------------------------------------------------
# Staged changes detection
# -----------------------------------------------------------------------

class TestStagedChanges:
    """Agent finds PII in git diff --staged."""

    def test_email_in_staged_file(self, person_md, repo_with_staged_pii):
        """Finds a PERSON.md email in a staged file."""
        result = run_privacy_guard(repo_with_staged_pii, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        email_findings = [f for f in result["findings"]
                          if _e("zanzibar", "quux.example") in f.get("matched_value", "")]
        assert len(email_findings) > 0

    def test_staged_finding_has_location(self, person_md, repo_with_staged_pii):
        """Staged findings include a location reference."""
        result = run_privacy_guard(repo_with_staged_pii, person_md_path=person_md)

        findings_with_location = [f for f in result["findings"]
                                  if f.get("location")]
        assert len(findings_with_location) > 0


# -----------------------------------------------------------------------
# Unstaged changes detection
# -----------------------------------------------------------------------

class TestUnstagedChanges:
    """Agent finds PII in git diff (unstaged tracked changes)."""

    def test_email_in_unstaged_change(self, person_md, repo_with_unstaged_pii):
        """Finds a PERSON.md email in an unstaged modification."""
        result = run_privacy_guard(repo_with_unstaged_pii, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        email_findings = [f for f in result["findings"]
                          if _e("zanzibar", "quux.example") in f.get("matched_value", "")]
        assert len(email_findings) > 0


# -----------------------------------------------------------------------
# Unpushed commits detection
# -----------------------------------------------------------------------

class TestUnpushedCommits:
    """Agent finds PII in unpushed commit diffs and messages."""

    def test_email_in_unpushed_commit_diff(self, person_md, repo_with_unpushed_pii):
        """Finds PII in the diff of an unpushed commit."""
        result = run_privacy_guard(repo_with_unpushed_pii, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        email_findings = [f for f in result["findings"]
                          if _e("zanzibar", "quux.example") in f.get("matched_value", "")]
        assert len(email_findings) > 0

    def test_pii_in_unpushed_commit_message(self, person_md, repo_with_pii_in_commit_message):
        """Finds PII in an unpushed commit message."""
        result = run_privacy_guard(repo_with_pii_in_commit_message, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        matched = " ".join(f.get("matched_value", "") for f in result["findings"])
        assert "Zanzibar" in matched or "Quuxville" in matched


# -----------------------------------------------------------------------
# Scope boundaries — agent should NOT find these
# -----------------------------------------------------------------------

class TestScopeBoundaries:
    """Agent respects pre-push scope — doesn't scan beyond diffs."""

    def test_clean_repo_no_findings(self, person_md, clean_repo):
        """Clean repo with no diffs or unpushed commits has zero findings."""
        result = run_privacy_guard(clean_repo, person_md_path=person_md)

        assert result["status"] == "completed"
        assert len(result["findings"]) == 0

    def test_pushed_pii_not_found(self, person_md, repo_pii_already_pushed):
        """PII that's already pushed is NOT flagged (no diff, no unpushed)."""
        result = run_privacy_guard(repo_pii_already_pushed, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        # The email is in a committed+pushed file — no diff should show it
        email_findings = [f for f in result["findings"]
                          if _e("zanzibar", "quux.example") in f.get("matched_value", "")]
        assert len(email_findings) == 0

    def test_does_not_read_individual_files(self, person_md, repo_pii_already_pushed):
        """Agent should not run git ls-files or Read individual files."""
        result = run_privacy_guard(repo_pii_already_pushed, person_md_path=person_md)

        # If the agent read files, it would find PII. Since it shouldn't,
        # zero findings confirms it's only looking at diffs.
        assert len(result["findings"]) == 0


# -----------------------------------------------------------------------
# Untracked files warning
# -----------------------------------------------------------------------

class TestUntrackedFiles:
    """Agent warns about untracked files it cannot scan."""

    def test_untracked_files_trigger_warning(self, person_md, repo_with_untracked_files):
        """Untracked files cause a partial status or warning."""
        result = run_privacy_guard(repo_with_untracked_files, person_md_path=person_md)

        assert result["status"] == "partial"
        warnings = " ".join(result.get("warnings", []))
        assert "untracked" in warnings.lower() or "scratch.txt" in warnings


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
        assert "scan_scope" in result or "summary" in result

    def test_failed_scan_has_required_fields(self, clean_repo):
        """Failed scan (missing PERSON.md) still emits structured JSON."""
        bogus = clean_repo.parent / "nope" / "PERSON.md"
        result = run_privacy_guard(clean_repo, person_md_path=bogus)

        assert result["status"] == "failed"
        assert "findings" in result
        assert isinstance(result["findings"], list)
        assert len(result["findings"]) == 0

    def test_scan_scope_reflects_what_was_checked(self, person_md, repo_with_staged_pii):
        """scan_scope reports staged/unstaged/unpushed counts."""
        result = run_privacy_guard(repo_with_staged_pii, person_md_path=person_md)

        scope = result.get("scan_scope", {})
        # Should indicate staged changes were checked
        assert scope.get("staged_changes") is True or "staged" in str(scope).lower()
