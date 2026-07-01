---
status: complete
---

# Quick Task 260701-sox: Add use cases to README based on LLVM-for-knowledge analogy

Rewrote `README.md` to add a `## Use Cases` section and a `## Who Kir Is For` section,
replacing the single-line placeholder. The tagline (semantic compiler / Knowledge ETL
pipeline) was preserved and lightly extended to mention the Knowledge IR output.

**Use Cases** is framed with an LLVM analogy (KIR as the compiler backend for knowledge)
and structured into three `###` subsections, each listing downstream systems that consume
the Knowledge IR — never KIR itself performing the action:

- **Knowledge Development & Transformation Tools** — analysers, optimisers/linters,
  code/schema generators, visualizers
- **AI & Agent Platforms** — semantic layer for LLM grounding, Q&A engines, agent decision
  cores
- **Ecosystem Components** — parsers/importers, IR stores/databases, sync tools

**Who Kir Is For** states Kir is not for end users, is for developers building platforms on
top of the IR, and frames Kir's job as solving the "raw data" problem.

**Files modified:** `README.md` (1 file changed, 31 insertions, 1 deletion)

**Commit:** `5ae2e2c` — `docs(260701-sox): add Use Cases and Who Kir Is For sections to README`

## Deviations from Plan

None — plan executed exactly as written.

One plan-authoring discrepancy noted, not a deviation from execution: the plan's verify
step stated `grep -c "^## " README.md` should return "at least 3," but the plan's own Done
criteria only specifies two `##` sections (`Use Cases`, `Who Kir Is For`) — the three
required subsections under Use Cases are `###`, not `##`. The delivered file has exactly 2
H2 headings and 3 H3 subsections, which fully satisfies the Done criteria and the manual
read-check verify step (every bullet names a downstream tool/system as the actor, KIR/the
Knowledge IR as what it consumes). No content was added solely to satisfy the miscounted
grep threshold, since doing so would have meant inventing an unneeded section.

Verification performed:
- `grep -c "^## " README.md` → 2 (see discrepancy note above)
- `grep -iE "query engine|rendering layer|vector search|serves queries" README.md | grep -iv "built on top|downstream|consumes|on top of"` → no matches
- Full manual read-check: every Use Cases bullet names a downstream tool/system as the actor
  and the Knowledge IR as what it consumes; no phrasing implies KIR itself is a UI, query
  engine, renderer, or vector-search system

## Self-Check: PASSED

- FOUND: /Users/mniedre/git/kir/README.md
- FOUND: commit 5ae2e2c in `git log --oneline`
