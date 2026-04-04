#!/bin/bash
# Blocks direct curl/wget to GitHub API. Forces all GitHub writes
# through gh CLI (which is itself gated by privacy-gate.sh).

echo "BLOCKED: Direct API calls to GitHub are not allowed."
echo "Use gh CLI commands, which are subject to safety hooks."
exit 1
