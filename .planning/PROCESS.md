# Process

Project-management instructions for how `.planning/` documents evolve. This is about managing the project, not about KIR the product — kept separate from PROJECT.md so that document stays a stable product/architecture reference.

## PROJECT.md Evolution

**After each phase transition** (via `/gsd-transition`):
1. "Product Definition" still accurate? → Update if drifted
2. Decisions to log? → Add to Architectural Decisions
3. Milestone boundary crossed? → Update ## Milestones (mark current, advance "(current)" marker)

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of PROJECT.md and REQUIREMENTS.md
2. Core Value check — still the right priority?
3. Audit Out of Scope (in REQUIREMENTS.md) — reasons still valid?
4. Update Context with current state
5. Rewrite ROADMAP.md for the next milestone's phases (pulling from REQUIREMENTS.md's "Future Milestone Scope" section for that milestone)

## REQUIREMENTS.md Evolution

**After each phase completes:**
1. Mark covered requirements as Complete in the relevant milestone section
2. Update traceability status
3. Note any requirements that changed scope

**After roadmap updates:**
1. Verify all current-milestone requirements still mapped
2. Add new requirements if scope expanded
3. Move requirements to v2/out of scope if descoped

## ROADMAP.md Evolution

ROADMAP.md holds only the current milestone's phases. When a milestone completes, ROADMAP.md is rewritten (not appended to) for the next milestone, pulling phase scope from PROJECT.md's ## Milestones table and requirement detail from REQUIREMENTS.md's corresponding "Future Milestone Scope" section.

---
*Created: 2026-06-29, split out of PROJECT.md's former "## Evolution" section to keep PROJECT.md a pure product/architecture document.*
