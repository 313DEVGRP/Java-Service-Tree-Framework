# Check Cache Bugs (CC#40524)

Audit your Claude Code setup for three cache bugs discovered in March 2026 that can silently inflate API costs by 10-20x.

**Time**: ~20 seconds | **Scope**: version, config files, CLAUDE.md, skills, hooks, shell profiles, all claude binaries

**Reference**: `anthropics/claude-code#40524` | **Discovered by**: `u/skibidi-toaleta-2137` (r/ClaudeAI) + `@whiletrue0x` (GitHub)

---

## Background

Three independent bugs cause Claude Code's prompt cache to break silently:

- **Bug 1** (standalone binary, v2.1.36+, edge case): A native string replacement in Anthropic's custom Bun/Zig fork is baked into the Zig HTTP header builder at the native layer — invisible from JavaScript, fires after `JSON.stringify` but before TLS. On every `/v1/messages` request, it searches the JSON body for the first occurrence of `cch=00000` and replaces it with a 5-char body hash. In normal usage only `system[0]` is affected (which has `cache_control: null`), so no cache impact. It only breaks cache if `cch=00000` leaks into `messages[]` — from a CLAUDE.md discussing the mechanism, a tool reading the CC bundle source, or the user typing it literally. 62 real-project transcripts verified: zero accidental leaks in normal usage.
- **Bug 2** (v2.1.69+): The `deferred_tools_delta` attachment introduced in v2.1.69 causes `messages[0]` to differ between fresh and resumed sessions, independently breaking cache prefix matching on every `--resume` or `--continue`. Confirmed still present in v2.1.88.
- **Bug 3** (v2.1.69+, widest impact): `cli.js` injects `x-anthropic-billing-header` as the first system prompt block, containing a per-conversation hash (3-char SHA-256 of first user message + version) that changes on every new session and every subagent call. This causes a full `cache_creation` on the system prompt (~12K tokens) instead of `cache_read` on every session start and Agent invocation. A/B tested: cache hit ratio goes from 48% to 99.98% with the env var fix.

Status: partial fix shipped in v2.1.88 (tool schema bytes). Bugs 2 and 3 still active as of v2.1.88.

---

## Instructions

You are an auditor. Run all phases in order, collect every result, and produce the final report. Do not skip phases or stop early.

---

### Phase 1 — Claude Code version and install method

```bash
# Version check
claude --version

# All installed claude binaries
which -a claude 2>/dev/null

# Check if active binary is standalone or npm
file $(which claude) 2>/dev/null
ls -la $(which claude) 2>/dev/null
```

- Version >= 2.1.36 AND standalone binary → flag **BUG 1 MECHANISM PRESENT** (edge case, only triggers if sentinel in messages)
- Version >= 2.1.69 → flag **BUG 2 RISK** and **BUG 3 RISK**
- Binary is Mach-O / ELF executable → standalone → **Bug 1 mechanism present**
- Binary is a symlink to `node_modules` or contains `cli.js` → npm/npx → **Bug 1 does not apply**

---

### Phase 2 — Sentinel scan (Bug 1)

Search for the literal string `cch=` in all static config files. Exclude `.jsonl` files (ephemeral conversation history) and this command file itself.

```bash
# Global config files
grep -r "cch=" \
  ~/.claude/CLAUDE.md \
  ~/.claude/MEMORY.md \
  ~/.claude/TONE.md \
  ~/.claude/FLAGS.md \
  ~/.claude/RULES.md \
  ~/.claude/RTK.md \
  ~/.claude/ANTI_AI.md \
  2>/dev/null

# Global skills, commands, agents, hooks (excluding this command file)
grep -rl "cch=" ~/.claude/skills/ 2>/dev/null
grep -rl "cch=" ~/.claude/commands/ --exclude="check-cache-bugs.md" 2>/dev/null
grep -rl "cch=" ~/.claude/agents/ 2>/dev/null
grep -rl "cch=" ~/.claude/hooks/ 2>/dev/null

# Project-level config
grep -r "cch=" CLAUDE.md .claude/CLAUDE.md .claude/MEMORY.md 2>/dev/null
grep -rl "cch=" .claude/skills/ 2>/dev/null
grep -rl "cch=" .claude/commands/ --exclude="check-cache-bugs.md" 2>/dev/null
grep -rl "cch=" .claude/agents/ 2>/dev/null
grep -rl "cch=" .claude/hooks/ 2>/dev/null

# Broader scan: all CLAUDE.md files across projects
find ~ -name "CLAUDE.md" \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  2>/dev/null | xargs grep -l "cch=" 2>/dev/null
```

Flag as **BUG 1 RISK** if any match found outside `.jsonl` files.

---

### Phase 3 — Resume/continue usage (Bug 2)

```bash
# settings.json
grep -i -- "--resume\|--continue" ~/.claude/settings.json 2>/dev/null
grep -i -- "--resume\|--continue" .claude/settings.json 2>/dev/null

# Hooks
grep -rn -- "--resume\|--continue" ~/.claude/hooks/ 2>/dev/null
grep -rn -- "--resume\|--continue" .claude/hooks/ 2>/dev/null

# Commands and skills
grep -rn -- "--resume\|--continue" ~/.claude/commands/ 2>/dev/null
grep -rn -- "--resume\|--continue" .claude/commands/ 2>/dev/null

# Shell profiles (aliases, functions)
grep -n -- "--resume\|--continue" ~/.zshrc ~/.bashrc ~/.bash_profile ~/.zprofile 2>/dev/null

# Project scripts
find . -name "*.sh" -o -name "Makefile" 2>/dev/null | \
  xargs grep -l -- "--resume\|--continue" 2>/dev/null
```

- Any hit in hooks/settings → flag **BUG 2 AUTOMATED** (constant exposure)
- Any hit in commands/skills/scripts → flag **BUG 2 MANUAL** (exposure when invoked)

---

### Phase 4 — Attribution header check (Bug 3)

Check whether the billing header env var is already disabled.

```bash
# Global settings
grep -i "CLAUDE_CODE_ATTRIBUTION_HEADER\|ENABLE_TOOL_SEARCH" \
  ~/.claude/settings.json 2>/dev/null

# Project settings
grep -i "CLAUDE_CODE_ATTRIBUTION_HEADER\|ENABLE_TOOL_SEARCH" \
  .claude/settings.json 2>/dev/null

# Shell profiles
grep -i "CLAUDE_CODE_ATTRIBUTION_HEADER" \
  ~/.zshrc ~/.bashrc ~/.bash_profile ~/.zprofile 2>/dev/null
```

- `CLAUDE_CODE_ATTRIBUTION_HEADER` not set to `false` AND version >= 2.1.69 → flag **BUG 3 ACTIVE**
- Already set to `false` → **BUG 3 MITIGATED**

---

### Phase 5 — Multiple binaries check

```bash
for b in $(which -a claude 2>/dev/null | sort -u); do
  echo "=== $b ==="
  $b --version 2>/dev/null || echo "unavailable"
  file $b 2>/dev/null
  ls -la $b 2>/dev/null
done
```

Flag any standalone binary >= 2.1.69 as at risk for all three bugs.
Note stale npm binaries that could be mistakenly invoked.

---

## Output Format

```
## Claude Code Cache Bug Audit — CC#40524

**Date**: [today]
**Active claude version**: [version]
**Install method**: [standalone binary | npm/npx | mixed]

---

### Bug 1 — Sentinel replacement (standalone binary v2.1.36+, edge case)
**Status**: [SAFE / AT RISK / NOT APPLICABLE]

**Mechanism active (standalone binary >= v2.1.36)**: [YES / NO]
**Trigger sentinel found in static config**: [YES — locations | NO]

[If AT RISK] `cch=00000` found in static config files:
- [file path]: [matching line]
→ Fix: remove the `cch=00000` string from those files.
→ Temporary workaround: `npx @anthropic-ai/claude-code` (npm package uses standard Bun, no replacement).
→ Note: sentinel in `.jsonl` conversation history is normal and harmless — only static config matters.

[If SAFE] Mechanism present in binary but no trigger in static config. Normal usage unaffected.
[If NOT APPLICABLE] npm/npx install — Bug 1 mechanism absent at the binary level.

---

### Bug 2 — Cache prefix mismatch on --resume / --continue (v2.1.69+)
**Status**: [SAFE / AT RISK (automated) / AT RISK (manual) / NOT APPLICABLE]

**Version in affected range (>= 2.1.69)**: [YES / NO]
**Automated usage (hooks/settings)**: [YES — locations | NO]
**Manual usage (commands/skills/scripts)**: [YES — locations | NO]

**Root cause**: `deferred_tools_delta` attachment introduced in v2.1.69 causes `messages[0]` to differ between fresh and resumed sessions, breaking cache prefix matching independently of Bug 1.

[If AT RISK]
→ Avoid `--resume` and `--continue` until fix ships.
→ Downgrade workaround: `npm install -g @anthropic-ai/claude-code@2.1.68` (last version before regression)

[If NOT APPLICABLE] Version < 2.1.69 — not affected.

---

### Bug 3 — Attribution header per-session hash (widest impact)
**Status**: [ACTIVE / MITIGATED / NOT APPLICABLE]

**Version in affected range (>= 2.1.69)**: [YES / NO]
**CLAUDE_CODE_ATTRIBUTION_HEADER=false already set**: [YES / NO]

[If ACTIVE] Every session start and every subagent call misses the system prompt cache (~12K tokens rebuilt at cache_creation rate).
→ Fix: add to ~/.claude/settings.json:
  {
    "env": {
      "CLAUDE_CODE_ATTRIBUTION_HEADER": "false",
      "ENABLE_TOOL_SEARCH": "false"
    }
  }
→ Expected impact: cache hit ratio 48% → ~99.98% (measured, source: @whiletrue0x CC#40524)

[If MITIGATED] Header already disabled. No action needed.
[If NOT APPLICABLE] Version < 2.1.69 — not affected.

---

### Multiple binaries
[List each binary found, version, type (standalone/npm), and per-bug status]

---

### Summary

| Bug | Impact | Status | Action |
|-----|--------|--------|--------|
| Bug 1 — sentinel in config | Edge case | [SAFE / AT RISK / N/A] | [action or "none"] |
| Bug 2 — --resume/--continue | Per-resume cache miss | [SAFE / AT RISK / N/A] | [action or "none"] |
| Bug 3 — attribution header | Every session + subagent | [ACTIVE / MITIGATED / N/A] | [action or "none"] |
| Stale binaries | — | [CLEAN / PRESENT] | [remove or none] |

[If Bug 3 ACTIVE — always show this]
⚡ Quick win: add CLAUDE_CODE_ATTRIBUTION_HEADER=false to settings.json — immediate effect, no restart needed.

[If all SAFE/MITIGATED/N/A]
✅ No active exposure. Re-run after updating Claude Code.

⚠️ Track fixes: github.com/anthropics/claude-code/issues/40524
```
