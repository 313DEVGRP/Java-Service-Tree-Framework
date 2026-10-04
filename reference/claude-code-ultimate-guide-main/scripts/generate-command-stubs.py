#!/usr/bin/env python3
"""
Generate redirect stubs in examples/commands/ pointing to their examples/skills/ equivalents.

In Claude Code 2.1.3, commands were unified into skills. This script replaces each
command file with a short stub that preserves GitHub URLs while directing users to the
canonical skill location.

Usage:
    python3 scripts/generate-command-stubs.py          # Generate all stubs
    python3 scripts/generate-command-stubs.py --check  # Verify targets exist, no writes
    python3 scripts/generate-command-stubs.py --dry-run  # Show what would be written
"""

import os
import sys

BASE = "/Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide"
SRC = os.path.join(BASE, "examples/commands")
DST_SKILLS = os.path.join(BASE, "examples/skills")

ALREADY_STUB_MARKER = "Moved to Skills"

# Mapping: (src_rel, skill_name_or_subpath)
# skill_name_or_subpath is relative to examples/skills/
MIGRATIONS = [
    ("audit-codebase.md",      "audit-codebase/SKILL.md"),
    ("autoresearch.md",        "autoresearch/SKILL.md"),
    ("canary.md",              "canary/SKILL.md"),
    ("catchup.md",             "catchup/SKILL.md"),
    ("check-cache-bugs.md",    "check-cache-bugs/SKILL.md"),
    ("commit.md",              "commit/SKILL.md"),
    ("diagnose.md",            "diagnose/SKILL.md"),
    ("explain.md",             "explain/SKILL.md"),
    ("generate-tests.md",      "generate-tests/SKILL.md"),
    ("git-worktree.md",        "git-worktree/SKILL.md"),
    ("git-worktree-clean.md",  "git-worktree-clean/SKILL.md"),
    ("git-worktree-remove.md", "git-worktree-remove/SKILL.md"),
    ("git-worktree-status.md", "git-worktree-status/SKILL.md"),
    ("investigate.md",         "investigate/SKILL.md"),
    ("land-and-deploy.md",     "land-and-deploy/SKILL.md"),
    ("methodology-advisor.md", "methodology-advisor/SKILL.md"),
    ("optimize.md",            "optimize/SKILL.md"),
    ("pr.md",                  "pr/SKILL.md"),
    ("qa.md",                  "qa/SKILL.md"),
    ("recipe-template.md",     "recipe-template/SKILL.md"),
    ("refactor.md",            "refactor/SKILL.md"),
    ("release-notes.md",       "release-notes/SKILL.md"),
    ("review-plan.md",         "review-plan/SKILL.md"),
    ("review-pr.md",           "review-pr/SKILL.md"),
    ("routines-discover.md",   "routines-discover/SKILL.md"),
    ("sandbox-status.md",      "sandbox-status/SKILL.md"),
    ("scaffold.md",            "scaffold/SKILL.md"),
    ("security-audit.md",      "security-audit/SKILL.md"),
    ("security-check.md",      "security-check/SKILL.md"),
    ("security.md",            "security/SKILL.md"),
    ("session-save.md",        "session-save/SKILL.md"),
    ("ship.md",                "ship/SKILL.md"),
    ("sonarqube.md",           "sonarqube/SKILL.md"),
    ("update-threat-db.md",    "update-threat-db/SKILL.md"),
    ("validate-changes.md",    "validate-changes/SKILL.md"),
    # CI namespace
    ("ci/all.md",      "ci-all/SKILL.md"),
    ("ci/pipeline.md", "ci-pipeline/SKILL.md"),
    ("ci/status.md",   "ci-status/SKILL.md"),
    ("ci/tests.md",    "ci-tests/SKILL.md"),
    # Handoff namespace
    ("handoff/create-handoff.md", "handoff-create/SKILL.md"),
    ("handoff/resume-handoff.md", "handoff-resume/SKILL.md"),
    ("handoff/update-handoff.md", "handoff-update/SKILL.md"),
    # Learn namespace
    ("learn/alternatives.md", "learn-alternatives/SKILL.md"),
    ("learn/quiz.md",         "learn-quiz/SKILL.md"),
    ("learn/teach.md",        "learn-teach/SKILL.md"),
    # Plan pipeline — map to plan-pipeline/<stage>/
    ("plan-ceo-review.md",  "plan-pipeline/ceo-review/SKILL.md"),
    ("plan-eng-review.md",  "plan-pipeline/eng-review/SKILL.md"),
    ("plan-execute.md",     "plan-pipeline/execute/SKILL.md"),
    ("plan-start.md",       "plan-pipeline/start/SKILL.md"),
    ("plan-validate.md",    "plan-pipeline/validate/SKILL.md"),
]


def relative_skill_link(src_rel, skill_rel):
    """Compute the relative path from the stub to the skill file."""
    src_depth = src_rel.count("/")
    prefix = "../" * (src_depth + 1)  # +1 to go up from commands/ to examples/
    return f"{prefix}skills/{skill_rel}"


def build_stub(src_rel, skill_rel):
    skill_name = skill_rel.split("/")[0]  # e.g. "pr" from "pr/SKILL.md"
    rel_link = relative_skill_link(src_rel, skill_rel)
    return f"""# Moved to Skills

This command was migrated to a skill in Claude Code 2.1.3. See: [`examples/skills/{skill_rel}`]({rel_link})

Existing `.claude/commands/` files remain backward-compatible. For new projects, use the skill version.
"""


def is_already_stub(filepath):
    try:
        with open(filepath, "r") as f:
            return ALREADY_STUB_MARKER in f.read(200)
    except FileNotFoundError:
        return False


check_only = "--check" in sys.argv
dry_run = "--dry-run" in sys.argv

ok = 0
missing_target = 0
already_stub = 0
errors = []

for src_rel, skill_rel in MIGRATIONS:
    src_file = os.path.join(SRC, src_rel)
    target_skill = os.path.join(DST_SKILLS, skill_rel)

    # Verify target skill exists
    if not os.path.exists(target_skill):
        print(f"  MISSING TARGET: examples/skills/{skill_rel}")
        errors.append(src_rel)
        missing_target += 1
        continue

    # Skip if already a stub
    if is_already_stub(src_file):
        already_stub += 1
        continue

    stub_content = build_stub(src_rel, skill_rel)

    if check_only:
        print(f"  OK (target exists): {src_rel} -> examples/skills/{skill_rel}")
        ok += 1
    elif dry_run:
        print(f"  WOULD WRITE: {src_rel}")
        print(f"    -> examples/skills/{skill_rel}")
        ok += 1
    else:
        with open(src_file, "w") as f:
            f.write(stub_content)
        print(f"  STUB: {src_rel} -> examples/skills/{skill_rel}")
        ok += 1

print()
if check_only:
    print(f"Check: {ok} OK, {missing_target} missing targets, {already_stub} already stubs")
elif dry_run:
    print(f"Dry run: {ok} would be written, {missing_target} missing targets, {already_stub} already stubs")
else:
    print(f"Done: {ok} stubs written, {missing_target} missing targets, {already_stub} already stubs")

if errors:
    print(f"\nERRORS (missing skill targets):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
