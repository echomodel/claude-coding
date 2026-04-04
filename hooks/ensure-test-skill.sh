#!/bin/bash
# Injects sociable-unit-tests skill content into agent context on first
# test file write per session. Uses session_id from stdin JSON to track
# injection state.

set -euo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))")

DATA_DIR="${CLAUDE_PLUGIN_DATA:-/tmp/claude-coding-plugin}"
MARKER_DIR="$DATA_DIR/sessions/$SESSION_ID"
MARKER="$MARKER_DIR/test-skill-injected"

# Already injected this session — allow silently
if [ -f "$MARKER" ]; then
    exit 0
fi

# First test file write this session — inject skill content
mkdir -p "$MARKER_DIR"
touch "$MARKER"

SKILL_PATH="${CLAUDE_PLUGIN_ROOT}/skills/sociable-unit-tests/SKILL.md"
if [ ! -f "$SKILL_PATH" ]; then
    # Skill not vendored yet — allow without injection
    exit 0
fi

SKILL_CONTENT=$(cat "$SKILL_PATH")

cat <<ENDJSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "IMPORTANT: You are about to write test files. The following testing guidelines are mandatory for this project:\n\n${SKILL_CONTENT}"
  }
}
ENDJSON
