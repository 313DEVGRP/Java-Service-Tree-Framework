#!/bin/bash
# Pre-commit hook: Verify VERSION file consistency across the repo
# Used by: .pre-commit-config.yaml

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
VERSION_FILE="$REPO_ROOT/VERSION"

# Read the canonical version
if [ ! -f "$VERSION_FILE" ]; then
  echo "❌ VERSION file not found at $VERSION_FILE"
  exit 1
fi

CANONICAL_VERSION=$(cat "$VERSION_FILE" | tr -d '\n')

# Check files that should contain the version
declare -a FILES_TO_CHECK=(
  "$REPO_ROOT/guide/ultimate-guide.md"
  "$REPO_ROOT/guide/cheatsheet.md"
  "$REPO_ROOT/README.md"
  "$REPO_ROOT/machine-readable/reference.yaml"
)

ERRORS=0

for FILE in "${FILES_TO_CHECK[@]}"; do
  if [ ! -f "$FILE" ]; then
    continue
  fi

  if grep -q "$CANONICAL_VERSION" "$FILE" 2>/dev/null; then
    echo "✓ $FILE has version $CANONICAL_VERSION"
  else
    echo "❌ $FILE does NOT contain version $CANONICAL_VERSION"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ $ERRORS -gt 0 ]; then
  echo ""
  echo "⚠️  Version mismatch detected. Run:"
  echo "   ./scripts/sync-version.sh"
  exit 1
fi

exit 0
