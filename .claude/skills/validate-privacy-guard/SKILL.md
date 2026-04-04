---
name: validate-privacy-guard
description: >-
  Run privacy-guard agent integration tests. Use when the user says
  "validate privacy guard", "test the agent", "run privacy guard tests",
  or after modifying agents/privacy-guard.md.
---

# Validate Privacy Guard

Run the integration tests for the privacy-guard agent. These tests
invoke the real agent via `claude --agent` against temporary git repos
with planted PII and verify the structured JSON output.

## How to run

**Always run one test method at a time** unless the user explicitly
asks for a batch or parallel run. Each test spawns a real agent that
takes 1-3 minutes. Running them all at once gives no feedback for
10+ minutes and wastes tokens if early tests fail.

### Single test (default)

```bash
.venv-test/bin/pytest tests/integration/privacy_guard/ -k <test_name>
```

### With debug logging

```bash
PRIVACY_GUARD_DEBUG=1 .venv-test/bin/pytest tests/integration/privacy_guard/ -k <test_name>
```

Debug logs go to `/tmp/privacy-guard-tests/<repo-name>.log` (harness)
and `<repo-name>.claude-debug.log` (Claude internals). Watch with:

```bash
tail -f /tmp/privacy-guard-tests/*.log
```

### Batch (only when user asks)

```bash
make test-privacy-guard
```

This runs all tests in parallel with 5 workers. Only do this when
individual tests are passing and you want a full regression check.

## Setup (one time)

If `.venv-test/` doesn't exist:

```bash
python3 -m venv .venv-test
.venv-test/bin/pip install pytest pytest-xdist
```

## Test execution order

Run tests in this order to catch problems early and cheaply:

1. `test_missing_person_md` — agent fails fast, ~15s
2. `test_clean_repo_no_findings` — agent scans but finds nothing, ~2m
3. `test_email_in_file` — basic pattern detection, ~2m
4. `test_name_in_file` — name detection, ~2m
5. `test_financial_provider_in_file` — financial provider, ~2m
6. `test_property_name_in_file` — property name, ~2m
7. `test_history_not_scanned_by_default` — confirms opt-in behavior
8. `test_pii_in_prior_commit_when_asked` — history scan when requested
9. `test_pii_in_commit_message` — PII in commit message text
10. `test_pii_in_gitignored_file` — gitignored file warning
11. `test_author_email_domain_mismatch` — mismatched author
12. `test_os_username_in_file` — OS-level detection (env_dependent)
13. `test_unknown_name_in_personal_context` — judgment call (may xfail)
14. `test_completed_scan_has_required_fields` — JSON schema
15. `test_failed_scan_has_required_fields` — failure JSON schema
16. `test_exhaustive_reporting` — slow, runs last

Stop at the first failure, diagnose, and fix before proceeding.

## After a failure

1. Check the debug log: `cat /tmp/privacy-guard-tests/<repo>.log`
2. Look at the raw agent output — is structured JSON present?
3. If JSON is missing, the agent didn't follow its instructions
4. If JSON is present but findings are wrong, check categories and
   matched_value fields against what was planted in the fixture
5. Fix the agent .md or the test fixture, not both at once

## What these tests DON'T cover

- Real PERSON.md values (tests use fictitious data)
- GitHub issues/PRs (no remote in test repos)
- Private repo inventory (no gh access in test repos)
- Full history scanning performance on large repos
