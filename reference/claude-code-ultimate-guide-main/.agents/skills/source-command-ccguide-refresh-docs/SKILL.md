---
name: "source-command-ccguide-refresh-docs"
description: "Re-fetch official Anthropic Codex docs and update current snapshot (baseline unchanged)"
---

# source-command-ccguide-refresh-docs

Use this skill when the user asks to run the migrated source command `ccguide-refresh-docs`.

## Command Template

Use the `refresh_official_docs` MCP tool.

This fetches ~1.2MB from Anthropic (takes ~5s) and updates only the "current" snapshot.
The baseline (set by init_official_docs) is never touched.

After success, show the quick diff preview against the baseline that the tool returns.
Remind the user to run /ccguide:diff-docs for the full detailed diff.
