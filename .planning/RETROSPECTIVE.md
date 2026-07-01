# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — M1: Deterministic Document Compiler

**Shipped:** 2026-07-01
**Phases:** 3 (1, 2, 2.1) | **Plans:** 10 | **Tasks:** 22

### What Was Built
- Hexagonal core: frozen, `extra=forbid` Pydantic domain model (Concept, Relation, Taxonomy, Document, Conflict) with zero LLM/filesystem/YAML imports, behind four typed Protocol ports
- `graphlib`-based `PassRegistry` resolving execution order from declared dependencies, plus a frozen `CompilerContext` DI container and structured (never-printed) diagnostics
- `YamlFileRepository` — first permanent adapter, one YAML file per artifact, path-traversal-safe
- End-to-end Document Compiler: Markdown → Document IR via 4 registered passes (Parse, Section, Metadata, ExtractConcepts), with an async LLM-backed extraction pass depending only on `LLMPort`
- Deterministic LLM caching keyed on (checksum, prompt version, schema version, model id); golden-fixture tests with zero live API calls
- Closed the STOR-01/STOR-02 persistence gap: `DocumentCompiler.compile()` now saves through `RepositoryPort` on every call

### What Worked
- Fakes-first proof strategy (Phase 1 proved port-substitutability and pipeline mechanics entirely with fakes before any real adapter existed) caught design issues early and made Phase 2's real adapters low-risk
- Golden-fixture/replay testing for the LLM extraction pass kept the whole suite fast (123 tests in 0.18s) and CI-safe (zero live API calls)
- TDD RED/GREEN with an explicit "no-edit-existing-files" proof for EXT-01 gave a concrete, checkable artifact for an otherwise hard-to-verify extensibility requirement

### What Was Inefficient
- STOR-01/STOR-02 were proven only against fakes in Phase 1 and not wired into the real `DocumentCompiler` service until a reactive gap-closure phase (2.1) was inserted after Phase 2 — the integration checker should have caught this at Phase 2 planning time, not after
- `from __future__ import annotations` / `TYPE_CHECKING` crept into 4 Phase 1 source files and 25 test files despite STYLE_GUIDE.md prohibiting both — the rule existed before the violations were written, suggesting the style guide wasn't consulted during scaffolding or was easy to forget mid-implementation
- REQUIREMENTS.md traceability table status column ("Pending") was never updated as requirements were satisfied, and ROADMAP.md's Phase 2.1 progress row was left stale ("In progress") after completion — both required manual correction at milestone-close time rather than being kept current incrementally

### Patterns Established
- Cross-phase gap closure via an inserted phase (e.g. "2.1") rather than reopening Phase 2 — keeps phase history intentional and auditable
- Quick tasks (`.planning/quick/`) as the vehicle for post-hoc doc/style fixes discovered after a phase closes, rather than reopening phase plans

### Key Lessons
1. When a requirement is proven only against fakes in an earlier phase (e.g. STOR-01/STOR-02 in Phase 1), explicitly plan its real-adapter wiring into the phase that introduces the real service — don't assume it's implied and defer discovery to milestone audit.
2. Style-guide compliance (STYLE_GUIDE.md rules like no-`__future__`-imports, no-TYPE_CHECKING) needs an automated lint/CI check, not just a written rule — manual adherence during fast-moving implementation predictably drifts.
3. Update REQUIREMENTS.md/ROADMAP.md status fields at the moment work completes, not retroactively at milestone close — batching the correction makes the milestone audit do avoidable bookkeeping work.

### Cost Observations
- Sessions: multiple across 2026-06-29 to 2026-07-01 (3-day timeline)
- Commits: 138 total in repo history at milestone close
- Notable: fakes-first Phase 1 + golden-fixture Phase 2 kept the full 123-test suite running in 0.18s with zero live LLM calls, making iteration cost near-zero during development

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | multiple (3 days) | 3 (incl. 1 inserted gap-closure) | Introduced gap-closure-phase pattern (2.1) and quick-task pattern for post-close doc/style fixes |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|---------------------|
| v1.0 | 123 | not measured | Domain model (zero LLM/FS/YAML imports), 4 Protocol ports |

### Top Lessons (Verified Across Milestones)

1. Prove port-substitutability and pipeline mechanics with fakes before writing any real adapter — de-risks later integration.
2. Requirements proven only against fakes need an explicit "wire the real thing" task in the next phase that introduces the real service, not an implicit assumption.
