---
name: changelog
description: View recent CHANGELOG entries
argument-hint: "[count]"
---

# CHANGELOG Viewer

Display recent entries from CHANGELOG.md with optional count limit.

## Usage

```
/changelog       # Show last 5 entries (default)
/changelog 10    # Show last 10 entries
/changelog all   # Show all entries
```

## What to Display

Read `CHANGELOG.md` and extract the last N version entries with:
- Version number
- Release date
- All sections (Added, Changed, Fixed, etc.)
- Full content per section

## Output Format

```
📋 Recent CHANGELOG Entries

═══════════════════════════════════════════════════════════

## [3.9.11] - 2026-01-20

### Added
- Production Safety Rules (Section 14.3)
  - Critical safety practices for production deployments
  - Rollback procedures and monitoring guidelines

### Documentation
- Enhanced deployment workflow documentation
- Added safety checklist templates

═══════════════════════════════════════════════════════════

## [3.9.10] - 2026-01-19

### Added
- DevOps & SRE Guide with FIRE Framework
  - Fault tolerance patterns
  - Incident response protocols
  - Recovery procedures
  - Escalation guidelines

### Documentation
- New Section 9.18: DevOps & SRE Practices
- 45+ operational best practices

═══════════════════════════════════════════════════════════

[... more entries ...]

───────────────────────────────────────────────────────────
Showing 5 of N total entries
Use /changelog 10 for more, or /changelog all for complete history
```

## Implementation

1. Read CHANGELOG.md
2. Parse entries using regex: `## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})`
3. Extract content between version headers
4. Limit to N entries (default 5)
5. Format with clear separators
6. Add footer with total count

## Special Handling

- Skip `[Unreleased]` section if present at top
- Handle missing dates gracefully
- Preserve markdown formatting in descriptions
- Show section hierarchy (###, bullet points)
