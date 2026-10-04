#!/usr/bin/env python3
"""Migrate examples/commands/ -> examples/skills/ with updated frontmatter."""

import os
import re

BASE = "/Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide"
SRC = os.path.join(BASE, "examples/commands")
DST = os.path.join(BASE, "examples/skills")

# (src_rel, new_name, effort, disable_model_invocation, extra_fields)
# extra_fields: overrides for model/allowed-tools
MIGRATIONS = [
    # Root-level
    ("audit-codebase.md",      "audit-codebase",      "medium", True,  {}),
    ("autoresearch.md",        "autoresearch",         "high",   True,  {}),
    ("canary.md",              "canary",               "medium", True,  {}),
    ("catchup.md",             "catchup",              "low",    True,  {}),
    ("check-cache-bugs.md",    "check-cache-bugs",     "low",    True,  {}),
    ("commit.md",              "commit",               "low",    True,  {}),
    ("diagnose.md",            "diagnose",             "medium", True,  {}),
    ("explain.md",             "explain",              "low",    False, {}),
    ("generate-tests.md",      "generate-tests",       "medium", True,  {}),
    ("git-worktree.md",        "git-worktree",         "medium", True,  {}),
    ("git-worktree-clean.md",  "git-worktree-clean",   "low",    True,  {}),
    ("git-worktree-remove.md", "git-worktree-remove",  "low",    True,  {}),
    ("git-worktree-status.md", "git-worktree-status",  "low",    True,  {}),
    ("investigate.md",         "investigate",          "medium", True,  {}),
    ("land-and-deploy.md",     "land-and-deploy",      "high",   True,  {}),
    ("methodology-advisor.md", "methodology-advisor",  "medium", False, {}),
    ("optimize.md",            "optimize",             "medium", True,  {}),
    ("pr.md",                  "pr",                   "medium", True,  {}),
    ("qa.md",                  "qa",                   "high",   True,  {}),
    ("recipe-template.md",     "recipe-template",      "low",    True,  {}),
    ("refactor.md",            "refactor",             "medium", True,  {}),
    ("release-notes.md",       "release-notes",        "medium", True,  {}),
    ("review-plan.md",         "review-plan",          "medium", True,  {}),
    ("review-pr.md",           "review-pr",            "medium", True,  {}),
    ("routines-discover.md",   "routines-discover",    "medium", True,  {}),
    ("sandbox-status.md",      "sandbox-status",       "low",    True,  {}),
    ("scaffold.md",            "scaffold",             "medium", True,  {}),
    ("security-audit.md",      "security-audit",       "high",   True,  {}),
    ("security-check.md",      "security-check",       "low",    True,  {}),
    ("security.md",            "security",             "medium", True,  {}),
    ("session-save.md",        "session-save",         "low",    True,  {}),
    ("ship.md",                "ship",                 "medium", True,  {}),
    ("sonarqube.md",           "sonarqube",            "medium", True,  {}),
    ("update-threat-db.md",    "update-threat-db",     "high",   True,  {}),
    ("validate-changes.md",    "validate-changes",     "low",    True,  {}),
    # CI namespace -> ci-*
    ("ci/all.md",      "ci-all",      "medium", True, {"model": "haiku", "allowed-tools": "[Bash]"}),
    ("ci/pipeline.md", "ci-pipeline", "low",    True, {"model": "haiku", "allowed-tools": "[Bash]"}),
    ("ci/status.md",   "ci-status",   "low",    True, {"model": "haiku", "allowed-tools": "[Bash]"}),
    ("ci/tests.md",    "ci-tests",    "low",    True, {"model": "haiku", "allowed-tools": "[Bash]"}),
    # Handoff namespace -> handoff-*
    ("handoff/create-handoff.md", "handoff-create", "low", True, {}),
    ("handoff/resume-handoff.md", "handoff-resume", "low", True, {}),
    ("handoff/update-handoff.md", "handoff-update", "low", True, {}),
    # Learn namespace -> learn-* (exploration, no disable flag)
    ("learn/alternatives.md", "learn-alternatives", "low", False, {}),
    ("learn/quiz.md",         "learn-quiz",         "low", False, {}),
    ("learn/teach.md",        "learn-teach",        "low", False, {}),
]


def parse_frontmatter(content):
    """Return (frontmatter_dict_as_text, body). frontmatter_dict_as_text is None if no frontmatter."""
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            return content[4:end], content[end + 5:]
    return None, content


def get_field(fm_text, field):
    """Extract a single-line field value from frontmatter text. Returns None if absent."""
    if not fm_text:
        return None
    # Match field: value or field: "value"
    m = re.search(rf"^{re.escape(field)}:\s*(.+)$", fm_text, re.MULTILINE)
    if m:
        v = m.group(1).strip()
        # Strip surrounding quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        return v
    return None


def build_frontmatter(new_name, src_fm, effort, disable, extra):
    description = get_field(src_fm, "description") or ""
    argument_hint = get_field(src_fm, "argument-hint")
    allowed_tools = extra.get("allowed-tools") or get_field(src_fm, "allowed-tools")
    model = extra.get("model")

    lines = ["---", f"name: {new_name}"]
    if description:
        # Re-quote descriptions with special chars
        if any(c in description for c in [':', '#', '{', '[']):
            lines.append(f'description: "{description}"')
        else:
            lines.append(f"description: {description}")
    if argument_hint:
        if any(c in argument_hint for c in [':', '{', '[']):
            lines.append(f'argument-hint: "{argument_hint}"')
        else:
            lines.append(f"argument-hint: {argument_hint}")
    if allowed_tools:
        lines.append(f"allowed-tools: {allowed_tools}")
    if model:
        lines.append(f"model: {model}")
    lines.append(f"effort: {effort}")
    if disable:
        lines.append("disable-model-invocation: true")
    lines.append("---")
    return "\n".join(lines)


created = 0
skipped = 0

for src_rel, new_name, effort, disable, extra in MIGRATIONS:
    src_file = os.path.join(SRC, src_rel)
    dst_dir = os.path.join(DST, new_name)
    dst_file = os.path.join(dst_dir, "SKILL.md")

    if not os.path.exists(src_file):
        print(f"  SKIP (src not found): {src_rel}")
        skipped += 1
        continue

    if os.path.exists(dst_file):
        print(f"  SKIP (already exists): {dst_file}")
        skipped += 1
        continue

    with open(src_file, "r") as f:
        content = f.read()

    fm_text, body = parse_frontmatter(content)
    new_fm = build_frontmatter(new_name, fm_text, effort, disable, extra)
    new_content = new_fm + "\n" + body

    os.makedirs(dst_dir, exist_ok=True)
    with open(dst_file, "w") as f:
        f.write(new_content)

    print(f"  OK: {src_rel} -> {new_name}/SKILL.md")
    created += 1

print(f"\nDone: {created} created, {skipped} skipped")
