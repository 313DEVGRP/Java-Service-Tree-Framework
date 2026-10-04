#!/bin/bash
# Install: Security Suite plugin for Claude Code
# This script installs all security-related agents, commands, hooks, and templates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
PROJECT_CLAUDE_DIR="${CLAUDE_PROJECT_DIR:-.claude}"

echo "🔐 Installing Security Suite..."
echo ""

# Function to copy file with confirmation
copy_file() {
  local src="$1"
  local dest="$2"
  local type="$3"

  if [ ! -f "$src" ]; then
    echo "⚠️  Source not found: $src"
    return 1
  fi

  mkdir -p "$(dirname "$dest")"

  if [ -f "$dest" ]; then
    echo "  ⚠️  $type already exists at $dest"
    echo "     Backing up to ${dest}.bak"
    cp "$dest" "${dest}.bak"
  fi

  cp "$src" "$dest"
  echo "  ✓ Installed: $(basename "$dest") ($type)"
}

# 1. Install Agents
echo "📦 Installing Agents..."
copy_file "$SCRIPT_DIR/agents/security-auditor.md" "$PROJECT_CLAUDE_DIR/agents/security-auditor.md" "Agent"
echo ""

# 2. Install Commands
echo "📦 Installing Commands..."
copy_file "$SCRIPT_DIR/commands/security-check.md" "$PROJECT_CLAUDE_DIR/commands/security-check.md" "Command"
copy_file "$SCRIPT_DIR/commands/security-audit.md" "$PROJECT_CLAUDE_DIR/commands/security-audit.md" "Command"
copy_file "$SCRIPT_DIR/commands/audit-agents-skills.md" "$PROJECT_CLAUDE_DIR/commands/audit-agents-skills.md" "Command"
echo ""

# 3. Install Hooks
echo "📦 Installing Hooks..."
if [ -d "$SCRIPT_DIR/hooks/bash" ]; then
  for hook in "$SCRIPT_DIR"/hooks/bash/*.sh; do
    if [ -f "$hook" ]; then
      filename=$(basename "$hook")
      copy_file "$hook" "$PROJECT_CLAUDE_DIR/hooks/bash/$filename" "Hook"
      chmod +x "$PROJECT_CLAUDE_DIR/hooks/bash/$filename"
    fi
  done
fi

if [ -d "$SCRIPT_DIR/hooks/powershell" ]; then
  for hook in "$SCRIPT_DIR"/hooks/powershell/*.ps1; do
    if [ -f "$hook" ]; then
      filename=$(basename "$hook")
      copy_file "$hook" "$PROJECT_CLAUDE_DIR/hooks/powershell/$filename" "Hook"
    fi
  done
fi
echo ""

# 4. Install Templates/Skills
echo "📦 Installing Templates..."
if [ -d "$SCRIPT_DIR/templates" ]; then
  for template in "$SCRIPT_DIR"/templates/*.md; do
    if [ -f "$template" ]; then
      filename=$(basename "$template" .md)
      copy_file "$template" "$PROJECT_CLAUDE_DIR/skills/$filename/SKILL.md" "Skill"
    fi
  done
fi
echo ""

# 5. Update settings.json to enable hooks (if needed)
echo "⚙️  Updating configuration..."
if [ -f "$PROJECT_CLAUDE_DIR/settings.json" ]; then
  echo "  ✓ settings.json exists (review hooks section manually if needed)"
else
  echo "  ⚠️  settings.json not found at $PROJECT_CLAUDE_DIR/settings.json"
  echo "     Review installation guide for hook setup"
fi
echo ""

echo "✅ Security Suite installed successfully!"
echo ""
echo "🚀 Next steps:"
echo "  1. Review installed commands: ls $PROJECT_CLAUDE_DIR/commands/"
echo "  2. Quick test: /security-check"
echo "  3. Full audit: /security-audit"
echo "  4. Verify agents: /audit-agents-skills"
echo ""
echo "📖 Documentation: README.md in this directory"
echo ""
