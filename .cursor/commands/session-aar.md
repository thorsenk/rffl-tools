# Session AAR (After-Action Review)

## What is an AAR?

An **After-Action Review (AAR)** is a structured retrospective document that captures:
- What was planned vs. what actually happened
- What went well and what didn't
- Lessons learned and recommendations
- Metrics and outcomes
- Next steps

## Purpose

AARs serve as:
- **Knowledge capture** - Document decisions, challenges, and solutions for future reference
- **Learning tool** - Identify patterns, mistakes, and improvements
- **Project history** - Create a record of how features were built
- **Onboarding aid** - Help new contributors understand past work

## When to Create a Session AAR

Create a session AAR for:
- ✅ Significant coding sessions (2+ hours of focused work)
- ✅ Complex problem-solving sessions
- ✅ Architecture decisions or refactoring
- ✅ When you discover important patterns or gotchas
- ✅ Sessions with valuable lessons learned

Don't create for:
- ❌ Quick bug fixes
- ❌ Simple, routine tasks
- ❌ Sessions without notable outcomes

## Quick Session AAR Template

```markdown
# Session AAR - [Brief Description]

**Date:** YYYY-MM-DD
**Duration:** ~X hours
**Focus:** [What you worked on]

## What Was Planned
- [Goal 1]
- [Goal 2]

## What Actually Happened
- [What you accomplished]
- [What changed from plan]

## What Went Well
- [Success 1]
- [Success 2]

## Challenges / What Didn't Go Well
- [Challenge 1] → [How resolved]
- [Challenge 2] → [How resolved]

## Key Learnings
- [Technical insight]
- [Process insight]

## Next Steps
- [ ] [Action item]
- [ ] [Action item]

## Code/File Changes
- `path/to/file.py` - [What changed]
- `path/to/file.py` - [What changed]
```

## Full AAR Template (for Major Projects)

For major builds or multi-session projects, use the full template from `docs/aars/README.md`:
1. Executive Summary
2. Mission/Objective
3. Timeline
4. What Was Planned
5. What Actually Happened
6. What Went Well
7. What Didn't Go Well
8. Lessons Learned
9. Recommendations (Immediate, Short-term, Medium-term, Long-term)
10. Metrics & Outcomes
11. Next Steps
12. Conclusion

## Examples

- **Session AAR:** Quick retrospective of a single coding session
- **Project AAR:** Full review of a major feature build (see `docs/aars/AAR_2025-12-20_FORENSIC_AGENT_BUILD.md`)

---

**Reference:** See `docs/aars/README.md` for complete AAR guidelines and examples.

