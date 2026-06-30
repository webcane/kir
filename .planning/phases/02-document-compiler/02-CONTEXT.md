# Phase 2: Document Compiler - Context

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the Document Compiler: a single Markdown source compiles deterministically into a self-contained Document IR (id, title, source, checksum, language, sections, concepts, glossary, entities, references), through deterministic passes (Parse → Section → Metadata) plus one LLM-backed extraction pass (concepts/glossary/entities/references) that depends only on LLMPort. Concretely: real Markdown parsing, a real `PydanticAIAdapter` implementing `LLMPort` (alongside the existing fake), a Prompt Registry with prompt versioning, an LLM response cache built on Phase 1's generic Cache abstraction (keyed on document checksum + prompt version + schema version + pinned model id), and golden-fixture replay tests with zero live API calls in CI. Compiling two documents must never let one document's IR contain information from the other. No cross-document merging (alias resolution, concept merging, knowledge-level taxonomy/conflict detection) happens in this phase — that's Phase 3's Knowledge Compiler.

</domain>

<decisions>
## Implementation Decisions

### Section splitting (DOC-01)
- **D-01:** Sections are detected heading-based, at any heading level (H1–H6) — every heading starts a new section. Content appearing before the first heading becomes an untitled preamble section. Matches the `Parse → Section → Metadata` pipeline sketch already in ARCHITECTURE.md.

### Extraction call shape (DOC-03, LLM-01)
- **D-02:** The LLM extraction pass makes one combined structured-output call per document — a single Pydantic output model returns concepts, glossary terms, entities, and references together, rather than four separate LLMPort calls. Cheaper (1 LLM call/doc) and the categories are related enough that joint context likely improves extraction accuracy. This narrows ARCHITECTURE.md's `extract_concepts(sections) -> list[ExtractedConcept]` port-method sketch to one extraction method returning a combined structured result.

### Extraction failure handling (DOC-03, cross-cutting with Phase 1's D-01)
- **D-03:** If the LLM extraction pass fails for a document after PydanticAI's retries (`ModelRetry`/`output_retries`) are exhausted, the document still produces a Document IR with empty concepts/glossary/entities/references, and a structured Diagnostic error is recorded against that document. The document compile is never hard-failed by this pass — consistent with Phase 1's D-01 (pipeline always runs every pass to completion; halting is the caller's decision after inspecting diagnostics, never the pipeline's).

### Golden fixture corpus (LLM-03)
- **D-04:** The golden/replay fixture corpus for the extraction pass is small, hand-authored synthetic Markdown documents (a few sections each) with hand-crafted expected extraction output — not real excerpts from project docs. Easy to reason about, fast, deterministic, and sufficient for unit-level pass testing at this phase's scope.

### Claude's Discretion
- Concrete Markdown parser library choice (e.g. `mistune` vs `markdown-it-py` vs others) is left to research — not decided in STACK.md, and not a vision-level decision the user needs to make.
- Exact prompt versioning scheme (semver string, content hash, manual integer) is left to research/planning, grounded in the project's existing `prompt_version`-as-tracked-field convention.
- Exact cache adapter implementation built atop Phase 1's generic `Cache` Protocol (in-memory vs file-based for this phase) is left to research/planning — Phase 1's D-03 already scoped the Protocol itself as generic; this phase only needs to prove the LLM-specific cache-key construction works against it.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/PROJECT.md` — product definition, Architecture Principles, Product Boundary, Architecture & Workstreams
- `.planning/REQUIREMENTS.md` — full text for DOC-01..03, LLM-01..03 (the requirements this phase satisfies)
- `.planning/ROADMAP.md` §"Phase 2: Document Compiler" — goal, success criteria, sub-deliverables (Structured Output, Prompt Registry, Prompt Versioning, Provider Adapter, Caching, Replay Tests)

### Architecture
- `.planning/research/ARCHITECTURE.md` §"Recommended Project Structure" — `compiler/documents/` package layout (`parse.py`, `section.py`, `metadata.py`), `llm/` as its own package (prompt versioning, cache-key construction, provider substitutability)
- `.planning/research/ARCHITECTURE.md` (pipeline sketch around line 30, 195–240) — `Parse → Section → Metadata → ExtractConcepts(LLM)` pass chain, `@register_pass("extract_concepts", depends_on=("parse", "section", "metadata"))` example, `LLMPort.extract_concepts` Protocol sketch and `PydanticAIAdapter` implementation sketch
- `.planning/research/ARCHITECTURE.md` §"Anti-Patterns" — Anti-Pattern 3 (importing PydanticAI's `Agent` type directly into pass signatures instead of the narrower `LLMPort` interface)
- `.planning/research/ARCHITECTURE.md` (line ~309) — LLM response cache (`llm/cache.py`, keyed on document checksum + prompt version + schema version + model id) is a *required* Phase 2 mechanism, not a later optimization
- `.planning/research/STACK.md` — PydanticAI v2.0.0 API surface (renamed from v1: `result_type`→`output_type`, `.data`→`.output`, `result_retries`→`output_retries`); Tool Output mode recommended over Prompted Output; `TestModel`/`FunctionModel` for pass-logic unit tests, `pytest-recording` (VCR cassettes) for golden-fixture regression tests
- `.planning/research/SUMMARY.md` — research summary

### Prior phase context
- `.planning/phases/01-compiler-foundation/01-CONTEXT.md` — D-01 (diagnostics never halt the pipeline mid-run, carried forward as the basis for D-03 above), D-03 (generic Cache Protocol scope, extended here with LLM-specific cache-key logic per LLM-02)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/kir/core/ports/llm_port.py` — existing `LLMPort` Protocol from Phase 1; Phase 2 implements a real adapter against it (the contract itself may need a method-shape update per D-02's combined-extraction decision)
- `src/kir/core/ports/cache_port.py` — existing generic Cache Protocol from Phase 1 (D-03); Phase 2 builds the LLM-specific cache-key construction on top of this, does not replace it
- `src/kir/core/passes/registry.py`, `src/kir/core/passes/context.py`, `src/kir/core/passes/base.py` — Pass/PassRegistry/CompilerContext mechanics from Phase 1; new deterministic passes (Parse, Section, Metadata) and the LLM-backed extraction pass register against this existing mechanism without modification
- `src/kir/core/domain/models/document.py` — existing Document IR entity; Phase 2 populates it for real via the new passes instead of fakes
- `src/kir/tooling/repository/yaml_repository.py` — existing YAML-file-per-artifact repository adapter from Phase 1; available if Document IR artifacts need persisting during this phase's proofs

### Established Patterns
- Pass registration via `@register_pass(name, depends_on=(...))` decorator, topological execution order resolved at pipeline-build time (Phase 1 D-02)
- Ports as Protocols owned by domain; adapters live in `tooling/` or `llm/`, never imported into `core/`

### Integration Points
- New deterministic passes (`compiler/documents/parse.py`, `section.py`, `metadata.py`) and the LLM-backed extraction pass register into the same `PassRegistry` instance proven generically in Phase 1
- Real `PydanticAIAdapter` and fake LLM adapter both satisfy the same `LLMPort` Protocol from `src/kir/core/ports/llm_port.py`, swappable via `CompilerContext` exactly as Phase 1 proved with fakes

</code_context>

<specifics>
## Specific Ideas

No specific UI/behavior references — this is compiler infrastructure. The four decisions above (any-level heading sections; one combined extraction call; diagnostic-and-continue on extraction failure; small hand-authored synthetic fixtures) were all picked as the option most consistent with Phase 1's established philosophy (pipeline always completes; diagnostics over side effects; don't pre-build beyond what's needed) and ARCHITECTURE.md's existing pipeline sketch.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Cross-document concept merging, alias resolution, and knowledge-level taxonomy/conflict detection were confirmed (not newly raised) as Phase 3 scope per ROADMAP.md, not pulled forward.

</deferred>

---

*Phase: 2-Document Compiler*
*Context gathered: 2026-06-30*
