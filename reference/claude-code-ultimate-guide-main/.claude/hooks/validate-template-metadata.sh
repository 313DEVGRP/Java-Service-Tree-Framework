#!/bin/bash
# Hook: validate-template-metadata.sh
# Event: PreCommit
# Description: Validate that new/modified templates have proper metadata

set -euo pipefail

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Not in a git repository, skipping template metadata validation"
  exit 0
fi

# Find new or modified template files
TEMPLATE_EXTENSIONS=("md" "sh" "ps1")
TEMPLATE_DIRS=("examples/agents" "examples/commands" "examples/skills" "examples/hooks" "examples/workflows" "examples/scripts")

# Get staged files
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")

if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

# Check each template file
for file in $STAGED_FILES; do
  # Check if file is in examples/ and has a template extension
  is_template=false
  for dir in "${TEMPLATE_DIRS[@]}"; do
    if [[ "$file" == "$dir"/* ]]; then
      is_template=true
      break
    fi
  done

  if ! $is_template; then
    continue
  fi

  # Skip README and non-template files
  if [[ "$file" == */README.md ]] || [[ "$file" == *plugin.json ]]; then
    continue
  fi

  # Check if file exists
  if [ ! -f "$file" ]; then
    continue
  fi

  # Extract frontmatter
  if [[ "$file" == *.md ]]; then
    # Markdown: check for --- frontmatter
    if ! head -1 "$file" | grep -q "^---"; then
      echo -e "${RED}❌ Missing metadata in $file${NC}"
      echo "   Add YAML frontmatter at top with: name, description, complexity, time"
      ERRORS=$((ERRORS + 1))
    fi
  elif [[ "$file" == *.sh ]] || [[ "$file" == *.ps1 ]]; then
    # Shell: check for # --- metadata comment
    if ! head -3 "$file" | grep -q "# ---"; then
      echo -e "${YELLOW}⚠️  No metadata in $file${NC}"
      echo "   Consider adding: # --- name: template-name ... # ---"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
done

# Run Python validation if available
if command -v python3 &> /dev/null; then
  if [ -f "scripts/generate-template-catalog.py" ]; then
    # Only validate if templates directory was changed
    if echo "$STAGED_FILES" | grep -q "^examples/"; then
      python3 scripts/generate-template-catalog.py --validate 2>&1 | grep -v "^✅" || true
    fi
  fi
fi

if [ $ERRORS -gt 0 ]; then
  echo ""
  echo -e "${RED}❌ Template validation failed ($ERRORS errors)${NC}"
  echo "   See docs/template-metadata-schema.md for format requirements"
  exit 1
fi

if [ $WARNINGS -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}⚠️  Template validation passed with $WARNINGS warnings${NC}"
fi

exit 0
