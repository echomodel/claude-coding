.PHONY: test test-privacy-guard

test:
	pytest

test-privacy-guard:
	python3 -m venv .venv-test
	.venv-test/bin/pip install -q pytest pytest-xdist
	.venv-test/bin/pytest tests/integration/privacy_guard/ -n 5
