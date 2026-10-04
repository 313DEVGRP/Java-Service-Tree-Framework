---
name: audit-quiz-coverage
description: Find quiz coverage gaps from recent guide/CHANGELOG/CC-releases changes and propose new questions
argument-hint: "[category-id or 'all']"
---

# Quiz Coverage Audit: Propose New Questions from Recent Changes

Goal: read what changed recently in the guide and in Claude Code itself, cross-reference against the live quiz, and propose new questions for anything with no coverage yet. This is a **proposal-only** workflow: never auto-add questions to the live quiz without human review.

## Sources to read

1. `CHANGELOG.md` in this repo — `[Unreleased]` section plus the last 5-10 released entries, to see what guide content changed or was added recently.
2. `machine-readable/reference.yaml` — the guide's topic/section index (`deep_dive` keys), to know what's documented and where.
3. `machine-readable/claude-code-releases.yaml` — Claude Code's own version history (`latest`, `releases[]`, `breaking_summary`, `milestones`). Focus on the most recent 10-15 versions.
4. `guide/core/claude-code-releases.md` — human-readable version of the same, useful for full context on a specific release.

## Live quiz ground truth

The deployed quiz reads from:
`/Users/florianbruniaux/Sites/perso/claude-code-ultimate-guide-landing/src/content/questions/**/*.md`

16 categories (directory = category_id):
`01-quick-start`, `02-core-concepts`, `03-memory-settings`, `04-agents`, `05-skills`, `06-commands`, `07-hooks`, `08-mcp-servers`, `09-advanced-patterns`, `10-reference`, `11-learning-with-ai`, `12-architecture-internals`, `13-security-hardening`, `14-privacy-observability`, `15-ai-ecosystem`, `16-agent-harness-context`.

Question file schema (frontmatter + body):
```yaml
---
id: NN-NNN            # category-two-digit, question three-digit
category_id: N         # 1-16
difficulty: junior|intermediate|senior|power
profiles: [junior, senior, power, pm]   # subset
correct: a|b|c|d
options:
  a: "..."
  b: "..."
  c: "..."
  d: "..."
doc_reference:
  file: guide/....md   # must exist under the guide repo root
  section: "..."
  anchor: '#...'       # optional
official_doc: https://...   # optional
---

Question text here

---

Explanation text here
```

**YAML gotcha**: any option or field value containing a colon (`: `) MUST be wrapped in double quotes, or the frontmatter fails to parse (this broke the build twice during the last quiz audit, see `claudedocs/quiz-audit-2026-07-08/` for the incident).

## What to do

If `$ARGUMENTS` names a category id or slug, scope the gap analysis to that category only. If `$ARGUMENTS` is empty or `all`, cover every category.

For each category in scope:

1. Read every existing question's `question` text and `doc_reference` in that category's directory (id + question only, skip explanations, to keep this cheap) to know what's already covered.
2. Cross-reference against:
   - Any `[Unreleased]` or recent `CHANGELOG.md` entry describing a guide addition relevant to this category's topic.
   - Any `claude-code-releases.yaml` entry (recent versions) describing a new Claude Code feature, flag, default change, or behavior relevant to this category, that has no existing question about it.
   - Any `reference.yaml` `deep_dive` key for this topic whose linked guide section has no corresponding question.
3. Draft 2-5 NEW questions per category that fill a genuine gap (not a rephrase of an existing question). Each must:
   - Be non-trivial (tests understanding/application, not pure trivia).
   - Have exactly 4 plausible options with one verifiably correct answer (check the cited guide section yourself before finalizing).
   - Cite a real `doc_reference` (file that actually exists under the guide repo, section that actually supports the answer).
   - Prioritize recent (last 2-3 releases) Claude Code changes and recently-added guide sections over older, already-stable content.
4. One-line rationale per question: what gap it fills and why now (e.g. "v2.1.202 added X, no question covers it yet").

## Output

Write proposals to `claudedocs/quiz-coverage-audit-{today's date}/proposals-new-questions.md`, grouped by category, formatted as ready-to-paste frontmatter + question + explanation blocks matching the schema above, each with its rationale. Do not touch any file under `claude-code-ultimate-guide-landing/`. Do not commit or push anything.

At the end, print a short summary: categories scanned, gaps found, questions proposed per category, and any category where the CHANGELOG/releases mention something relevant but you weren't confident enough to draft a question (name the topic instead of guessing).
