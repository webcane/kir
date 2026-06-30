# Phase 1: Compiler Foundation - Context

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the compiler's infrastructure substrate, proven entirely with fakes — no real Markdown parsing, no real LLM calls, no real filesystem I/O. Concretely: the domain model (Concept, Relation, Taxonomy, Document, Diagnostic entities; ConceptId, RelationId, Checksum, SourceRef value objects), the three core ports (LLMPort, RepositoryPort, MarkdownParserPort) as Protocols, the Pass/PassRegistry/pipeline mechanics with dependency-driven ordering, a CompilerContext carrying ports + run metadata, structured Diagnostics, an Artifact Manifest, and a generic Cache abstraction. Success is demonstrated by writing trivial fake passes and fake adapters — not by compiling any real document. No real pass, parser, or LLM adapter is written in this phase (that's Phase 2).

</domain>

<decisions>
## Implementation Decisions

### Diagnostics behavior (CORE-06)
- **D-01:** The pipeline always runs every registered pass to completion regardless of diagnostic severity. Diagnostics (including Errors) accumulate across all passes; halting/failing the overall compile is a decision for the caller to make after inspecting the full diagnostics list, not something the pipeline does mid-run. Rationale: matches the Rust-compiler-style "structured diagnostics instead of side effects" framing already in PROJECT.md/ARCHITECTURE.md, and avoids one buggy pass masking diagnostics from later passes.

### Dependency graph failure mode (CORE-04 / PASS-05)
- **D-02:** Bad dependency declarations (a depends_on referencing an unregistered pass name, or a circular dependency) are detected at pipeline-build time — i.e. when `PassRegistry.pipeline()` runs its topological sort — not at individual `register_pass()` call time. Rationale: registration via decorator is import-order-dependent (per ARCHITECTURE.md Pattern 1), so validating at registration time would break if passes self-register out of order; validating at build time means the full graph is known and a single clear error (naming the cycle or the missing pass) can be raised once.

### Cache abstraction scope (cross-cutting, foreshadows LLM-02 in Phase 2)
- **D-03:** Phase 1's Cache Protocol is a generic key-value abstraction only — `get(key: str)` / `set(key: str, value: ...)` over opaque string keys. It does not know about LLM-specific concepts (checksum, prompt_version, schema_version, model_id). Phase 2's LLM response cache (LLM-02) builds its specific cache-key construction logic on top of this generic Protocol; Phase 1 must prove the abstraction is swappable (fake in-memory implementation) without coupling it to LLM concerns that don't exist yet in this phase.

### Artifact Manifest scope (cross-cutting, foreshadows Phase 5 incremental compilation)
- **D-04:** Phase 1's Artifact Manifest tracks only artifact id + version (which artifacts exist, what version produced them) — proven against fake artifacts. Checksum tracking and dependency-index tracking for incremental compilation are explicitly out of scope for Phase 1; they belong to Phase 5 (per ROADMAP.md's "Incremental compilation... sequenced after Validation, not earlier" decision). Do not pre-build the fuller schema now.

### Claude's Discretion
- Exact file/module layout for domain models, ports, passes, and config follows `.planning/research/ARCHITECTURE.md`'s "Recommended Project Structure" (5-package split: `core`, `compiler/documents`, `compiler/knowledge`, `llm`, `tooling`) unless research surfaces a concrete conflict during planning.
- Exact shape of the fake passes/adapters used to prove the mechanics (how many, what dependency graphs they exercise) is left to planning/research — the success criteria in ROADMAP.md (byte-identical reruns, dependency-driven ordering, swappable fakes for each port, one-YAML-file-per-artifact) are the bar, not a prescribed test list.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/PROJECT.md` — product definition, Architecture Principles, Product Boundary, Architecture & Workstreams, Architectural Decisions (esp. hexagonal architecture, Pydantic v2 as canonical IR, compiler-pass pipeline as extension mechanism)
- `.planning/REQUIREMENTS.md` — full text for CORE-01..07, PASS-01..05, EXT-01, STOR-01..02 (the requirements this phase satisfies)
- `.planning/ROADMAP.md` §"Phase 1: Compiler Foundation" — goal, success criteria, sub-deliverables (Pass Registry, Pipeline, Diagnostics model, Dependency Graph, Artifact Manifest, Cache abstraction)

### Architecture
- `.planning/research/ARCHITECTURE.md` §"Recommended Project Structure" — the 5-package split (`core`, `compiler/documents`, `compiler/knowledge`, `llm`, `tooling`) and import-boundary rules
- `.planning/research/ARCHITECTURE.md` §"Architectural Patterns" — Pattern 1 (Pass as pure function over ports, registered by decorator — includes a concrete `PassRegistry`/`CompilerContext` code sketch), Pattern 2 (Ports as Protocols owned by the domain), Pattern 3 (Repository per aggregate, YAML-file-per-artifact)
- `.planning/research/ARCHITECTURE.md` §"Anti-Patterns" — Anti-Pattern 1 (Leaky Hexagon: no adapter imports in domain), Anti-Pattern 2 (passes reaching around the registry to call each other directly)
- `.planning/research/SUMMARY.md` — research summary (read in full; cross-check against ARCHITECTURE.md for any since-superseded notes)
- `.planning/notes/five-package-split-with-core-first.md` — full decision record for the 5-package restructure referenced by ARCHITECTURE.md

</canonical_refs>

<code_context>
## Existing Code Insights

This is a greenfield phase — no `src/` directory exists yet, no `pyproject.toml`, no prior code to scout. There are no reusable assets, established patterns in code, or integration points to inventory; everything here is established by `.planning/research/ARCHITECTURE.md` instead of by reading existing source.

</code_context>

<specifics>
## Specific Ideas

No specific UI/behavior references — this is pure infrastructure. The closest things to "specific ideas" are the four decisions above (diagnostics never halt the pipeline mid-run; dependency-graph errors surface at build time, not registration time; cache stays generic in Phase 1; manifest stays minimal in Phase 1) — all picked as the lower-scope, less-coupled option in each case, consistent with the project's "don't pre-build for hypothetical future requirements" stance.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (LLM-specific cache-key shape and incremental-compilation manifest fields were explicitly discussed and deferred to Phase 2 and Phase 5 respectively, per D-03 and D-04 above — not new ideas, just confirming existing ROADMAP.md phase boundaries.)

</deferred>

---

*Phase: 1-Compiler Foundation*
*Context gathered: 2026-06-30*
