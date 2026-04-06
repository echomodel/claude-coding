"""Advanced integration tests for privacy-guard agent.

Tests source attribution, partial name matching, credential detection,
employer context judgment, and Google Drive ID detection. Each test
uses a realistic template repo (~20 clean Python files) with PII
injected into specific locations.

Values that would trip precommit scanners are built via concatenation
at runtime — never hardcoded as complete strings.
"""

import subprocess

import pytest

from .conftest import (
    FAKE_PERSON,
    _add_and_commit,
    _e,
    _init_git_repo,
    _populate_from_template,
    _stage_file,
    _modify_tracked_file,
    run_privacy_guard,
)


def _make_repo(test_root, name):
    """Create a template-populated repo with upstream."""
    repo = test_root / "repos" / name
    repo.mkdir(parents=True)
    _init_git_repo(repo, with_upstream=True)
    _populate_from_template(repo)
    subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
    return repo


# -----------------------------------------------------------------------
# Source attribution
# -----------------------------------------------------------------------

class TestSourceAttribution:
    """Findings should indicate WHERE the agent learned the value was sensitive."""

    def test_person_md_source_vs_os_runtime(self, person_md, test_root):
        """Email from PERSON.md should have source=person_md_frontmatter.
        OS username should have source=os_runtime. Both in one diff."""
        import os
        username = os.environ.get("USER", "")
        if not username or len(username) < 3:
            pytest.skip("OS username too short to test reliably")

        repo = _make_repo(test_root, "attribution-repo")
        # Stage a file with both PII types
        _stage_file(repo, "config/local.yaml",
                    "maintainer: " + _e("zanzibar", "quux.example") + "\n"
                    f"debug_path: /home/{username}/logs\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        sources = {f.get("source") for f in result["findings"]}
        # Should see at least person_md_frontmatter for the email
        assert "person_md_frontmatter" in sources, (
            f"Expected person_md_frontmatter in sources. Got: {sources}\n"
            f"Findings: {result['findings']}"
        )

    def test_contextual_judgment_source(self, person_md, test_root):
        """A credential-like string not from PERSON.md should get a
        non-person_md source attribution."""
        repo = _make_repo(test_root, "judgment-source-repo")
        # Stage a file with a fake API key (built via concat to avoid scanners)
        fake_key = "ghp_" + "R" * 18 + "x" * 18
        _stage_file(repo, "src/deploy.py",
                    "# deployment config\n"
                    f'API_TOKEN = "{fake_key}"\n'
                    "def deploy(): pass\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        token_findings = [f for f in result["findings"]
                          if fake_key in f.get("matched_value", "")
                          or "ghp_" in f.get("matched_value", "")
                          or f.get("category") == "credentials"]
        assert len(token_findings) > 0, (
            f"Expected to find GitHub PAT. Findings: {result['findings']}"
        )
        # Source should NOT be person_md_frontmatter
        for f in token_findings:
            assert f.get("source") != "person_md_frontmatter", (
                f"Token finding should not be attributed to person_md_frontmatter: {f}"
            )


# -----------------------------------------------------------------------
# Partial name matching
# -----------------------------------------------------------------------

class TestPartialNameMatch:
    """Agent should catch last names appearing alone, not just full names."""

    def test_last_name_only_in_comment(self, person_md, test_root):
        """'Quuxington' alone (not 'Zanzibar Quuxington') should be caught."""
        repo = _make_repo(test_root, "partial-name-repo")
        _stage_file(repo, "src/service.py",
                    "\"\"\"Widget service operations.\"\"\"\n"
                    "\n"
                    "# Reviewed by Quuxington — needs refactoring\n"
                    "def process():\n"
                    "    return True\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        name_findings = [f for f in result["findings"]
                         if "Quuxington" in f.get("matched_value", "")]
        assert len(name_findings) > 0, (
            f"Expected to find partial name 'Quuxington'. "
            f"Findings: {result['findings']}"
        )


# -----------------------------------------------------------------------
# Credential detection
# -----------------------------------------------------------------------

class TestCredentialDetection:
    """Agent should catch credentials/secrets even without PERSON.md patterns."""

    def test_gh_token_in_staged_config(self, person_md, test_root):
        """Fake GitHub PAT in staged file should be flagged."""
        repo = _make_repo(test_root, "cred-pat-repo")
        fake_pat = "ghp_" + "a" * 18 + "B" * 18
        _stage_file(repo, "config/secrets.yaml",
                    "server:\n"
                    "  port: 8080\n"
                    f"  github_token: {fake_pat}\n"
                    "  timeout: 30\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        cred_findings = [f for f in result["findings"]
                         if "ghp_" in f.get("matched_value", "")
                         or f.get("category") == "credentials"
                         or "token" in f.get("note", "").lower()]
        assert len(cred_findings) > 0, (
            f"Expected to find GitHub PAT. Findings: {result['findings']}"
        )

    def test_aws_key_in_unstaged_change(self, person_md, test_root):
        """Fake AWS access key in an unstaged modification."""
        repo = _make_repo(test_root, "cred-aws-repo")
        fake_aws = "AKIA" + "X" * 16
        _add_and_commit(repo, {
            "config/cloud.yaml": "provider: aws\nregion: us-east-1\n",
        }, "add cloud config")
        subprocess.run(["git", "push"], cwd=repo, check=True, capture_output=True)
        # Modify without staging
        _modify_tracked_file(repo, "config/cloud.yaml",
                             "provider: aws\n"
                             "region: us-east-1\n"
                             f"access_key: {fake_aws}\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        aws_findings = [f for f in result["findings"]
                        if "AKIA" in f.get("matched_value", "")
                        or f.get("category") == "credentials"
                        or "aws" in f.get("note", "").lower()]
        assert len(aws_findings) > 0, (
            f"Expected to find AWS key. Findings: {result['findings']}"
        )

    def test_google_drive_id_in_commit(self, person_md, test_root):
        """Fake Google Drive ID in an unpushed commit diff."""
        repo = _make_repo(test_root, "cred-drive-repo")
        # Google Drive IDs are 44-char base64-ish strings
        fake_id = "1BxiMVs0XRA5" + "nFMdKvBdBZjgm" + "UUqptlbs74OgVE2upms"
        _add_and_commit(repo, {
            "docs/resources.md": (
                "# Resources\n\n"
                "## Internal docs\n\n"
                f"- Design doc: https://docs.google.com/document/d/{fake_id}/edit\n"
                "- API spec: see docs/api.md\n"
            ),
        }, "add resource links")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        drive_findings = [f for f in result["findings"]
                          if fake_id in f.get("matched_value", "")
                          or "drive" in f.get("category", "").lower()
                          or "cloud" in f.get("category", "").lower()
                          or "document" in f.get("note", "").lower()
                          or "google" in f.get("note", "").lower()]
        assert len(drive_findings) > 0, (
            f"Expected to find Google Drive ID. Findings: {result['findings']}"
        )

    def test_private_key_header_in_staged(self, person_md, test_root):
        """PEM private key header in a staged file."""
        repo = _make_repo(test_root, "cred-pem-repo")
        # Build header via concat to avoid tripping scanners
        pem_header = "-----BEGIN " + "RSA PRIVATE" + " KEY-----"
        pem_footer = "-----END " + "RSA PRIVATE" + " KEY-----"
        _stage_file(repo, "keys/server.pem",
                    f"{pem_header}\n"
                    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n"
                    "FAKE KEY CONTENT FOR TESTING ONLY\n"
                    f"{pem_footer}\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        key_findings = [f for f in result["findings"]
                        if "private" in f.get("matched_value", "").lower()
                        or "key" in f.get("matched_value", "").lower()
                        or f.get("category") == "credentials"
                        or "private key" in f.get("note", "").lower()
                        or "pem" in f.get("note", "").lower()]
        assert len(key_findings) > 0, (
            f"Expected to find private key. Findings: {result['findings']}"
        )


# -----------------------------------------------------------------------
# Employer context judgment
# -----------------------------------------------------------------------

class TestEmployerContextJudgment:
    """Agent should distinguish employer-as-vendor from employer-as-employer."""

    def test_employer_as_vendor_not_flagged(self, person_md, test_root):
        """Referencing PERSON.md employer as a vendor/product should NOT
        be flagged. 'Megacorp LLC' is the test employer."""
        repo = _make_repo(test_root, "employer-vendor-repo")
        _stage_file(repo, "docs/architecture.md",
                    "# Architecture\n\n"
                    "## Infrastructure\n\n"
                    "We use Megacorp LLC Cloud Platform for hosting.\n"
                    "The Megacorp LLC API provides authentication.\n"
                    "Megacorp LLC SDK is pinned to v2.3.1.\n\n"
                    "## Alternatives considered\n\n"
                    "Evaluated Megacorp LLC vs other providers.\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        employer_findings = [f for f in result["findings"]
                             if "Megacorp" in f.get("matched_value", "")
                             and f.get("category") in ("employers", "employer_terms")]
        # Should NOT flag vendor references
        assert len(employer_findings) == 0, (
            f"Vendor references should not be flagged as employer findings. "
            f"Got: {employer_findings}"
        )

    def test_employer_as_employer_flagged(self, person_md, test_root):
        """Referencing PERSON.md employer in employment context SHOULD
        be flagged."""
        repo = _make_repo(test_root, "employer-employee-repo")
        _stage_file(repo, "docs/notes.md",
                    "# Project Notes\n\n"
                    "## Status\n\n"
                    "Widget service is ready for review.\n\n"
                    "## Context\n\n"
                    "Our team at Megacorp LLC ships this service weekly.\n"
                    "I got reassigned to the Megacorp LLC infra org.\n"
                    "The Megacorp LLC internal wiki has deployment docs.\n")

        result = run_privacy_guard(repo, person_md_path=person_md)

        assert result["status"] in ("completed", "partial")
        employer_findings = [f for f in result["findings"]
                             if "Megacorp" in f.get("matched_value", "")
                             or "employer" in f.get("category", "").lower()
                             or "employer" in f.get("note", "").lower()
                             or "team" in f.get("note", "").lower()
                             or "internal" in f.get("note", "").lower()]
        assert len(employer_findings) > 0, (
            f"Employment context should be flagged. Findings: {result['findings']}"
        )
