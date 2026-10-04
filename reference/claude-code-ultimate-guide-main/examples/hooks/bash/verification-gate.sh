#!/usr/bin/env bash
# verification-gate.sh — PostToolUse hook implementing the independent evaluator pattern.
# Runs after any file write or edit. Silent on success. Exits 2 with a message on failure.
#
# The independent evaluator principle: the agent that writes code should not be
# the same invocation that certifies it done. This hook acts as that second evaluator,
# reading exit codes without the charitable interpretation that context bias produces.
#
# Place in .claude/hooks/ and register as a PostToolUse hook in .claude/settings.json:
#
# "PostToolUse": [
#   {
#     "matcher": "Write|Edit",
#     "hooks": [{ "type": "command", "command": ".claude/hooks/verification-gate.sh" }]
#   }
# ]
#
# To adapt to another toolchain, replace LINT_CMD and TEST_CMD:
#   LINT_CMD="ruff check ."        # Python
#   TEST_CMD="pytest -q"           # Python
#   LINT_CMD="cargo clippy -q"     # Rust
#   TEST_CMD="cargo test -q"       # Rust

set -euo pipefail

# Override these via environment variables or edit directly below.
LINT_CMD="${LINT_CMD:-npm run lint --silent}"
TEST_CMD="${TEST_CMD:-npm test --silent}"

run_check() {
  local label="$1"
  local cmd="$2"

  if ! output=$(eval "$cmd" 2>&1); then
    echo "Verification gate: $label failed" >&2
    echo "$output" >&2
    exit 2
  fi
}

# Layer 1: lint (fastest — fail fast on syntax and style errors before running tests)
run_check "lint" "$LINT_CMD"

# Layer 2: tests (functional correctness of individual components and integration points)
run_check "tests" "$TEST_CMD"

# Silent exit on success. The agent sees no output and continues normally.
exit 0
