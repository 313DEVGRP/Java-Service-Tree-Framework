#!/usr/bin/env bash
# fix-whitepaper-blank-pages.sh
# Removes --- separators immediately before # (H1) headings in QMD whitepaper files.
# These separators are redundant (H1 already triggers a page break) and cause blank pages in Typst.
#
# Usage:
#   ./scripts/fix-whitepaper-blank-pages.sh           # dry run (shows what would change)
#   ./scripts/fix-whitepaper-blank-pages.sh --apply   # apply changes

set -euo pipefail

DRY_RUN=true
if [[ "${1:-}" == "--apply" ]]; then
  DRY_RUN=false
fi

WHITEPAPER_DIR="$(cd "$(dirname "$0")/.." && pwd)/whitepapers"
TOTAL_REMOVED=0
FILES_CHANGED=0

echo "=== Whitepaper Blank Page Fixer ==="
echo "Mode: $( [[ "$DRY_RUN" == true ]] && echo 'DRY RUN (use --apply to write changes)' || echo 'APPLYING CHANGES' )"
echo ""

# Process all QMD files in whitepapers/fr/ and whitepapers/en/
for dir in "$WHITEPAPER_DIR/fr" "$WHITEPAPER_DIR/en"; do
  [[ -d "$dir" ]] || continue

  for qmd in "$dir"/*.qmd; do
    [[ -f "$qmd" ]] || continue

    # Count --- before H1 headings (pattern: `---` on a line, optional blank lines, then `# ` heading)
    # Using awk to detect the pattern across lines
    count=$(awk '
      /^---$/ { sep_line = NR; sep = 1; next }
      /^$/ && sep { next }
      /^# / && sep { count++; sep = 0; next }
      { sep = 0 }
      END { print count+0 }
    ' "$qmd")

    if [[ "$count" -gt 0 ]]; then
      echo "  $(basename "$qmd") — $count separator(s) before H1 headings"

      if [[ "$DRY_RUN" == false ]]; then
        # Remove --- that are immediately before # headings
        # Logic: if a line is ---, check if next non-blank line starts with #
        # If yes, remove the ---
        python3 - "$qmd" <<'PYEOF'
import sys
import re

path = sys.argv[1]
with open(path, 'r') as f:
    lines = f.readlines()

output = []
i = 0
in_frontmatter = False
frontmatter_done = False

while i < len(lines):
    line = lines[i]

    # Handle YAML frontmatter: first --- opens it, second --- closes it
    # Never remove frontmatter delimiters
    if i == 0 and line.rstrip() == '---':
        in_frontmatter = True
        output.append(line)
        i += 1
        continue

    if in_frontmatter:
        output.append(line)
        if line.rstrip() == '---':
            in_frontmatter = False
            frontmatter_done = True
        i += 1
        continue

    # After frontmatter: remove --- that are immediately before # headings
    if frontmatter_done and line.rstrip() == '---':
        j = i + 1
        while j < len(lines) and lines[j].strip() == '':
            j += 1
        if j < len(lines) and re.match(r'^# ', lines[j]):
            # Skip this --- and the blank lines after it
            i = j
            continue

    output.append(line)
    i += 1

with open(path, 'w') as f:
    f.writelines(output)
PYEOF
        echo "    ✓ Fixed"
        FILES_CHANGED=$((FILES_CHANGED + 1))
      fi

      TOTAL_REMOVED=$((TOTAL_REMOVED + count))
    fi
  done
done

echo ""
echo "=== Summary ==="
echo "Separators to remove: $TOTAL_REMOVED"
if [[ "$DRY_RUN" == false ]]; then
  echo "Files modified: $FILES_CHANGED"
  echo ""
  echo "Next: rebuild affected whitepapers with:"
  echo "  cd whitepapers/fr && for f in *.qmd; do quarto render \"\$f\" --to whitepaper-typst; done"
else
  echo ""
  echo "Run with --apply to make changes."
fi
