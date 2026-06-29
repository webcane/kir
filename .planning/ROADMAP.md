# Roadmap: KIR (Knowledge Intermediate Representation)

**Current Milestone: M1 — Deterministic Document Compiler**

This roadmap covers only the current milestone's phases. M2 (Knowledge Compiler) and M3 (Production Semantic Compiler) are already scoped at the milestone level in `.planning/PROJECT.md` (## Milestones) and their requirements already exist in `.planning/REQUIREMENTS.md` (## M2/M3 — Future Milestone Scope), but their detailed phase plans are deliberately not written here yet. When M1 completes via `/gsd-complete-milestone`, this file is rewritten for M2's phases. See `.planning/PROJECT.md` (## Architecture & Workstreams) for the persistent cross-phase workstream view (Core, Document Compiler, Knowledge Compiler, Tooling, LLM Infrastructure) and the Artifact System cross-cutting thread — both apply across all milestones and are not repeated here.

## Overview

M1 is built bottom-up, compiler-style: domain model and pass-registry mechanics first (with zero LLM/filesystem dependencies, proven via fakes), then the per-document Document Compiler (deterministic passes plus a fake LLM adapter, and a real provider-backed adapter, for the extraction pass). This order is the user's own explicit design (KIR is their architecture), independently corroborated by research's suggested build order (domain+ports before passes, deterministic before LLM-backed).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Compiler Foundation** - Domain model, ports, CompilerContext, and pass-registry mechanics exist and are proven in isolation with fake passes, with zero LLM/filesystem/YAML imports in domain code
- [ ] **Phase 2: Document Compiler** - Markdown sources compile into Document IR end-to-end, through deterministic passes and one LLM-backed extraction pass, with a fake adapter proving LLMPort is swappable

## Phase Details

### Phase 1: Compiler Foundation
**Goal**: The domain model, ports, CompilerContext, and pass-registry mechanics exist and are proven correct in isolation — before any real pass, parser, or LLM adapter is written.
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, CORE-07, PASS-01, PASS-02, PASS-03, PASS-04, PASS-05, EXT-01, STOR-01, STOR-02
**Compiler Infrastructure delivered this phase** (concrete deliverables behind the requirements above, not new scope):
  - **Pass Registry** — decorator/plugin-based registration so new passes are added without editing existing ones (CORE-03, EXT-01)
  - **Pipeline** — dependency-resolved execution; pass order derived from declared consumes/produces, never hardcoded (CORE-04)
  - **Diagnostics model** — structured, Rust-compiler-style diagnostics (code, severity, location, suggestion) attached to pass output instead of printed/logged (CORE-06)
  - **Dependency Graph** — the same declared-dependency structure that orders Phase 1's pipeline is the foundation a later incremental-compilation milestone will walk to scope recompilation (CORE-04)
  - **Artifact Manifest** — the per-artifact manifest structure that a later phase populates with version info and another reads for change scoping (CORE-05, STOR-01; see PROJECT.md's Artifact System thread)
  - **Cache abstraction** — the CompilerContext-held cache interface that Phase 2's LLM response caching builds on (CORE-05)
**Success Criteria** (what must be TRUE):
  1. Domain modules (Concept, Relation, Taxonomy, Document entities; ConceptId, RelationId, Checksum, SourceRef value objects) import successfully with zero dependency on any LLM SDK, filesystem library, or YAML library
  2. A developer can write and register a new trivial CompilerPass (consuming one fake IR, producing another) without editing any existing pass or core pipeline file, and the pipeline executes it in the correct order purely from its declared dependencies
  3. Running the same set of fake passes twice against the same fake inputs produces byte-identical output artifacts, and each pass's output includes structured diagnostics (errors/warnings/infos) rather than printed/logged side effects
  4. A fake LLMPort, fake RepositoryPort, and fake MarkdownParserPort each satisfy their respective port contracts and can be swapped in CompilerContext without any domain or pass code change
  5. Writing a fake artifact through the repository port produces one individual YAML file per artifact (no monolithic JSON), in a directory that is verifiably separate from any raw-source directory
**Plans**: TBD

### Phase 2: Document Compiler
**Goal**: A single Markdown source compiles deterministically into a self-contained Document IR, including LLM-backed concept/glossary/entity/reference extraction, without merging information across documents.
**Depends on**: Phase 1
**Requirements**: DOC-01, DOC-02, DOC-03, LLM-01, LLM-02, LLM-03
**LLM Infrastructure delivered this phase** (a substantial standalone subsystem, not an incidental detail of the extraction pass — Workstream E):
  - **Structured Output** — the extraction pass returns validated, schema-checked (Pydantic) output rather than raw text (DOC-03)
  - **Prompt Registry** — extraction prompts are addressable, versioned artifacts rather than inline strings
  - **Prompt Versioning** — prompt version is one of the three keys (alongside checksum and schema version) that determines cache identity and reproducibility (LLM-02)
  - **Provider Adapter** — the concrete LLM SDK integration (e.g. PydanticAI-based) implements LLMPort as an interchangeable detail; a fake adapter and the real adapter are both swappable without touching pass code (LLM-01)
  - **Caching** — responses are cached/recorded keyed on (document checksum, prompt version, schema version, pinned model id), so reruns against unchanged inputs never re-call the LLM (LLM-02)
  - **Replay Tests** — the extraction pass's unit tests run entirely against recorded/mocked LLM responses (golden fixtures), with zero live API calls in CI (LLM-03)

  This thread is named explicitly so it is planned and built as its own subsystem — not absorbed into a single undifferentiated `extract.py` alongside Markdown parsing and section handling.
**Success Criteria** (what must be TRUE):
  1. Given a single Markdown file, the Document Compiler produces a Document IR containing id, title, source, checksum, language, sections, concepts, glossary, entities, and references
  2. Compiling two different Markdown files independently never causes either resulting Document IR to contain information from the other document
  3. The concept/glossary/entity/reference extraction pass depends only on LLMPort and returns a validated structured (Pydantic) output; a fake LLM adapter and a real provider-backed adapter both satisfy LLMPort and are swappable without touching pass code
  4. Re-running the extraction pass against an unchanged document (same checksum, prompt version, schema version, pinned model id) reproduces the identical cached output without re-calling the LLM
  5. The extraction pass's unit tests run entirely against recorded/mocked LLM responses (golden fixtures), with zero live API calls made during the test suite
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order within the current milestone: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Compiler Foundation | 0/TBD | Not started | - |
| 2. Document Compiler | 0/TBD | Not started | - |

**Next milestone (M2 — not yet detailed here):** Phase 3: Knowledge Compiler, Phase 4: Validation. See PROJECT.md ## Milestones for scope; REQUIREMENTS.md for the 17 requirements already defined for M2. Will be written into this file when M1 completes.
