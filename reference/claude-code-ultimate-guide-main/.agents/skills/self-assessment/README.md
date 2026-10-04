# Self-Assessment Skill

Interactive skill assessment tool that evaluates your Claude Code mastery and generates personalized learning paths.

## Overview

This skill provides two assessment modes:

- **Quick** (5 min): 10 questions, one per topic, rapid skill check
- **Comprehensive** (20 min): 20 questions, two per topic, deep mastery analysis

After assessment, get:
- ✓ Your mastery profile (Beginner/Intermediate/Advanced)
- ✓ Per-topic score breakdown
- ✓ Identified gaps ranked by importance
- ✓ Personalized learning path (respects dependencies)
- ✓ 3 practice projects matched to your level

## Usage

### Quick Assessment
```bash
/self-assessment quick
```
Fast evaluation across all topics. Shows overall level + top 2-3 gaps.

### Comprehensive Assessment
```bash
/self-assessment comprehensive
```
Deep dive into each topic. Shows detailed per-topic scores + full learning path + practice projects.

### Options
```bash
/self-assessment quick --verbose        # Show detailed explanations
/self-assessment comprehensive --save   # Save results to assessment-results.json
```

## How It Works

### Interaction Flow

1. **Choose mode:** Quick or Comprehensive
2. **Answer questions:** 4-option multiple choice (A-D)
3. **See feedback:** Explanation + guide link for each answer
4. **Get profile:** Mastery assessment across all topics
5. **Get learning path:** Personalized sequence respecting dependencies
6. **Choose action:** Learn, practice, retry, or deep-dive on specific topic

### Scoring

**Quick Mode:**
- 10 points total (1 per topic)
- Levels: 0-3 (Beginner), 4-7 (Intermediate), 8-10 (Advanced)

**Comprehensive Mode:**
- 20 points total (2 per topic)
- Levels: 0-6 (Beginner), 7-13 (Intermediate), 14-20 (Advanced)

### Topics Covered

1. Quick Start — Installation and basic workflow
2. Core Concepts — Interaction loop, context, sessions
3. Memory & Settings — CLAUDE.md configuration
4. Agents — Creating and using specialized agents
5. Skills — Building reusable capabilities
6. Commands — Slash commands and automation
7. Hooks — Event-driven triggers and validation
8. MCP Servers — Protocol integration and configuration
9. Advanced Patterns — Multi-agent orchestration, composition
10. Security & Production — Hardening, governance, scaling

## Output Examples

### Quick Mode Result
```
╔════════════════════════════════════════╗
║ Quick Assessment Results               ║
╠════════════════════════════════════════╣
║ Score: 7/10                            ║
║ Level: Intermediate Developer          ║
║                                        ║
║ Gaps (improve these):                  ║
║  • Hooks (didn't answer correctly)     ║
║  • MCP Servers (need training)         ║
║  • Advanced Patterns (not covered yet) ║
║                                        ║
║ Next Step:                             ║
║  1. Try /self-assessment comprehensive ║
║  2. Focus on: guide/ultimate-guide.md# ║
║     part-7-hooks                       ║
╚════════════════════════════════════════╝
```

### Comprehensive Mode Result
```
╔══════════════════════════════════════════════════════╗
║ Comprehensive Mastery Assessment                     ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║ 01 Quick Start           ██████░░░░  2/2  100%      ║
║ 02 Core Concepts         ████░░░░░░  1/2   50%      ║
║ 03 Memory & Settings     ██████░░░░  2/2  100%      ║
║ 04 Agents                ██░░░░░░░░  1/2   50%      ║
║ 05 Skills                ░░░░░░░░░░  0/2    0%      ║
║ 06 Commands              ████░░░░░░  1/2   50%      ║
║ 07 Hooks                 ░░░░░░░░░░  0/2    0%      ║
║ 08 MCP Servers           ██░░░░░░░░  1/2   50%      ║
║ 09 Advanced Patterns     ░░░░░░░░░░  0/2    0%      ║
║ 10 Security              ██░░░░░░░░  1/2   50%      ║
║                                                      ║
║ OVERALL: Intermediate (11/20 = 55%)                 ║
╚══════════════════════════════════════════════════════╝

Personalized Learning Path Generated (8-12 hours)
- Phase 1: Core Concepts (3 hours) [Required foundation]
- Phase 2: Skills & Hooks (4 hours) [After Phase 1]
- Phase 3: Advanced Patterns (3-4 hours) [After Phase 1 & 2]

3 Practice Projects assigned (see below)
```

## Learning Path

After comprehensive assessment, receive:

### Structured Learning Phases
- **Phase 1:** Fill critical gaps first (respects dependencies)
- **Phase 2:** Build intermediate skills
- **Phase 3:** Master advanced patterns and production
- **Bonus:** Deep-dive on specific weak topics

Each phase includes:
- 📖 Reading assignments (links to specific guide sections)
- 🔨 Hands-on practice (templates from examples/)
- 📝 Knowledge validation (/lesson-quiz [topic])

### 3 Practice Projects
Get real-world scenarios matched to your level:

1. **Project 1:** Combine 2-3 topics you're weak in (2-3 hours)
2. **Project 2:** Real-world workflow (3 hours)
3. **Project 3:** Production setup or team configuration (3 hours)

Each project includes:
- Clear success criteria
- Step-by-step instructions
- Expected outcomes

## Integration with Learning System

This skill works with `/lesson-quiz` for deeper learning:

```bash
# After comprehensive assessment, drill down:
/lesson-quiz 05-skills          # 5 questions on Skills topic
/lesson-quiz 07-hooks           # 5 questions on Hooks topic
/lesson-quiz 09-advanced        # 5 questions on Advanced Patterns
```

## Files in This Skill

- **SKILL.md** — Main skill definition and documentation
- **quick-assessment-prompt.txt** — Questions for quick mode (10 questions)
- **comprehensive-assessment-prompt.txt** — Questions for comprehensive mode (20 questions)
- **README.md** — This file

## Tips for Best Results

1. **Answer honestly** — Don't guess; skip if unsure (affects learning path quality)
2. **Review explanations** — Every answer includes why + guide link
3. **Retake after learning** — Your profile improves with each topic mastered
4. **Share results** — Use profile to align team training
5. **Tailor to your goal** — Quick for speed, Comprehensive for depth

## Scoring Distribution

### Quick Mode (10 questions, 1 per topic)
- Perfect score: 10/10 (100%) — Master level
- Advanced: 8-10/10 (80-100%)
- Intermediate: 4-7/10 (40-70%)
- Beginner: 0-3/10 (0-30%)

### Comprehensive Mode (20 questions, 2 per topic)
- Perfect score: 20/20 (100%) — Expert level
- Advanced: 14-20/20 (70-100%)
- Intermediate: 7-13/20 (35-65%)
- Beginner: 0-6/20 (0-30%)

Per-topic mastery:
- 0/2 (0%) — No mastery, focus here first
- 1/2 (50%) — Basic understanding, needs practice
- 2/2 (100%) — Proficient, ready for advanced

## Examples

### For a New Developer
```
Quick assessment → Identifies gaps in Core Concepts + Commands
→ Recommended: Read Part 2 + Part 6 of guide
→ Then try Quick assessment again
→ Move to Comprehensive assessment
```

### For an Intermediate Developer
```
Comprehensive assessment → Shows 50% on MCP + 0% on Hooks
→ Recommended learning path: Hooks Phase (4h) → MCP Phase (3h)
→ Practice Project: Automation workflow combining both
→ Then retry assessment to track improvement
```

### For Team Adoption
```
All team members take comprehensive assessment
→ Aggregate results show:
  • 80% need Hooks training
  • 50% need Advanced Patterns
  • 20% ready for security hardening
→ Create team learning plan from individual gaps
→ Monthly re-assessments track progress
```

## Future Enhancements

Planned features:
- [ ] Team aggregate reporting (see team gaps at a glance)
- [ ] Progress tracking (compare to previous assessment)
- [ ] Difficulty-adjusted questions (harder if you're scoring high)
- [ ] AI-tuned explanations (explain in your words)
- [ ] Export results (PDF profile, shareable with team leads)

## Getting Help

- **Questions about a question?** → Look at the explanation + guide link
- **Unsure about a topic?** → Use `/lesson-quiz [topic]` for follow-up
- **Want to understand gaps better?** → See personalized learning path
- **Ready to practice?** → Try one of the 3 assigned projects

---

**Start your assessment now:** `/self-assessment quick`
