#!/bin/bash
# Blocks git push and gh pr create unless invoked by the
# publish-pull-request skill. This is a hard safety gate.
#
# Currently blocks unconditionally — the publish-pull-request skill
# will need a bypass mechanism (env var or marker file) once we
# validate that hooks and tools share execution context.
#
# The bypass mechanism (env var or marker file) depends on whether
# hooks and tools share execution context — this is unverified.

echo "BLOCKED: Direct push/PR creation is not allowed."
echo "Use the publish-pull-request skill to publish your work."
echo ""
echo "If you are the publish-pull-request skill and seeing this,"
echo "the bypass mechanism needs to be implemented."
exit 1
