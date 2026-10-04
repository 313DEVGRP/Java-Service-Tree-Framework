---
name: update-releases
description: "Sync Claude Code releases from GitHub CHANGELOG to guide YAML + landing TypeScript"
argument-hint: "[--since <version>] [--dry-run]"
---

# Update Claude Code Releases

Fetch the latest Claude Code releases from the official GitHub CHANGELOG and sync both:
1. **Guide YAML**: `/Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide/machine-readable/claude-code-releases.yaml`
2. **Landing TS**: `/Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide-landing/src/data/releases.ts`

## Step 1: Parse Arguments

- `--since <version>` — process only versions strictly newer than this
- `--dry-run` — show planned changes, don't write anything
- No args — auto-detect from `latest:` field in current YAML

## Step 2: Read Current State

Read the guide YAML to get:
- `latest`: current latest version (e.g. "2.1.66")
- Full list of already-tracked versions

## Step 3: Fetch Official CHANGELOG

Use WebFetch to retrieve:
`https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`

Parse all `## X.Y.Z` blocks. For each block, extract:
- Version string (semver, no "v" prefix)
- All bullet points as the highlights list

## Step 4: Fetch Dates from npm Registry

For each new version detected, get the publish date from npm:

```bash
npm view @anthropic-ai/claude-code time --json 2>/dev/null
```

Parse the JSON to get ISO dates, convert to:
- YAML format: `YYYY-MM-DD`
- Landing format: `Mon D, YYYY` (e.g. `Mar 5, 2026`)

If npm fetch fails for a version, use today's date and note it.

## Step 5: Identify New Versions

Compare CHANGELOG versions against YAML. Versions in CHANGELOG but not in YAML are new.

If `--since <version>` was passed, only consider versions > that version.

Display to the user:
```
Current latest: v2.1.66
New versions found: N
  - 2.1.67 (Mar 5, 2026): [first highlight]
  - 2.1.68 (Mar 6, 2026): [first highlight]
```

If no new versions → display "Already up to date. Latest: vX.Y.Z" and exit.

If `--dry-run`, show the full planned diff for both files and exit without writing.

Ask: **"Update guide YAML + landing releases.ts? (y/n)"**

## Step 6: Update Guide YAML

Prepend new versions to the `releases:` array (newest first). Format each entry:

```yaml
- version: "X.Y.Z"
  date: "YYYY-MM-DD"
  highlights:
    - "⭐ Feature description"  # add ⭐ for: new commands, new MCP features, major additions
    - "Regular improvement"
    - "Fixed: bug description"
  breaking: []  # or list breaking changes if present
```

**⭐ heuristic**: Add ⭐ prefix if the highlight mentions a new slash command, new hook type, new API/env var, new MCP feature, or major workflow change. Bugfixes do NOT get ⭐.

Update top-level fields:
```yaml
latest: "X.Y.Z"  # newest version
updated: "YYYY-MM-DD"  # today
```

## Step 7: Update Landing releases.ts

Prepend new releases to the `releases` array. Format each entry:

```typescript
{
  version: 'vX.Y.Z',
  date: 'Mon D, YYYY',
  highlights: [
    '⭐ <strong>Feature Name</strong> — description with <code>command</code>',
    'Improvement description',
    'Fixed: bug description',
  ],
  latest: true,         // only on the newest version
  initiallyVisible: true,  // true if significant (has ⭐ or 3+ highlights), false if bugfix-only
  featured: true,          // only if has a ⭐ highlight
  featuredLabel: '⭐ Feature Name',  // label for the newest featured ⭐ item
},
```

**HTML formatting rules:**
- New slash commands → `<code>/command</code>`
- New env vars → `<code>ENV_VAR=value</code>`
- Technical terms → `<code>term</code>`
- Major features → `⭐ <strong>Name</strong> — description`
- Bugfixes start with → `Fixed: description`

**`latest` flag:** Set `latest: true` only on the newest version. Remove `latest: true` from the previous entry that had it.

**`initiallyVisible` logic:**
- `true` if: has ⭐ items, OR 3+ highlights, OR is the newest version
- `false` if: single bugfix/patch

## Step 8: Handle Breaking Changes

If any new version's highlights mention: "removed", "deprecated", "renamed", "migrated", "security fix", "breaking" → check if it should be added to `breakingChanges` in `releases.ts`.

If yes, append to `breakingChanges`:
```typescript
{ badge: 'Type', description: 'What changed with <code>code</code> (vX.Y.Z)' }
```

Badge options: `Security`, `Removed`, `OAuth`, `Install`, `Syntax`, `Behavior`

## Step 9: Summary

Show final summary:

```
✅ Guide YAML updated: +N versions (latest: vX.Y.Z)
✅ Landing releases.ts updated: +N releases
⚠️  Breaking changes added: [list if any, else "none"]

Next steps:
  cd /Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide
  git diff machine-readable/claude-code-releases.yaml

  cd /Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide-landing
  pnpm build  # validate before pushing
```
