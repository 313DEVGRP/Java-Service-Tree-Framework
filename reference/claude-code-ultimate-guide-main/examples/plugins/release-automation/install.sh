#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_CLAUDE_DIR="${CLAUDE_PROJECT_DIR:-.claude}"

echo "📦 Installing plugin..."

mkdir -p "$PROJECT_CLAUDE_DIR"/{agents,commands,skills,hooks/bash}

if [ -d "$SCRIPT_DIR/agents" ]; then
  cp "$SCRIPT_DIR"/agents/*.md "$PROJECT_CLAUDE_DIR/agents/" 2>/dev/null || true
fi

if [ -d "$SCRIPT_DIR/commands" ]; then
  cp "$SCRIPT_DIR"/commands/*.md "$PROJECT_CLAUDE_DIR/commands/" 2>/dev/null || true
fi

if [ -d "$SCRIPT_DIR/skills" ]; then
  cp "$SCRIPT_DIR"/skills/*.md "$PROJECT_CLAUDE_DIR/skills/" 2>/dev/null || true
fi

if [ -d "$SCRIPT_DIR/hooks/bash" ]; then
  cp "$SCRIPT_DIR"/hooks/bash/*.sh "$PROJECT_CLAUDE_DIR/hooks/bash/" 2>/dev/null || true
  chmod +x "$PROJECT_CLAUDE_DIR/hooks/bash/"*.sh 2>/dev/null || true
fi

echo "✅ Plugin installed successfully!"
echo "📖 See README.md for next steps"
