#!/bin/bash
# PostToolUse hook: Warn if VERSION file consistency is broken
# Runs after Edit/Write on VERSION or version-dependent files

set -euo pipefail

REPO_ROOT="${CLAUDE_PROJECT_DIR:-.}"
VERSION_FILE="$REPO_ROOT/VERSION"

# Only run if VERSION file exists
[ ! -f "$VERSION_FILE" ] && exit 0

CANONICAL_VERSION=$(cat "$VERSION_FILE" | tr -d '\n')

# Files to check
FILES_TO_CHECK=(
  "$REPO_ROOT/guide/ultimate-guide.md"
  "$REPO_ROOT/guide/cheatsheet.md"
  "$REPO_ROOT/README.md"
  "$REPO_ROOT/machine-readable/reference.yaml"
)

MISMATCHES=0

for FILE in "${FILES_TO_CHECK[@]}"; do
  [ ! -f "$FILE" ] && continue

  if ! grep -q "$CANONICAL_VERSION" "$FILE" 2>/dev/null; then
    MISMATCHES=$((MISMATCHES + 1))
  fi
done

if [ $MISMATCHES -gt 0 ]; then
  echo "⚠️  Version inconsistency detected in $MISMATCHES file(s)"
  echo ""
  echo "Run to fix:"
  echo "  ./scripts/sync-version.sh"
  echo ""
fi

exit 0
