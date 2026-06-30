# Roadmap: KIR (Knowledge Intermediate Representation)

## Current Milestone: M1 — Deterministic Document Compiler

This roadmap describes only the execution plan for the current milestone. Future milestones are defined in PROJECT.md (## Milestones).

## Milestone Exit Criteria

M1 is complete when:

- A deterministic Document Compiler exists.
- Every compiler pass is independently testable.
- Domain code has zero infrastructure dependencies.
- A Markdown document compiles into a valid Document IR.
- The LLM extraction pass works with both a fake and a real adapter through LLMPort.
- All acceptance tests pass.

## Execution Strategy

M1 is implemented bottom-up. Compiler infrastructure is completed before any concrete compiler pass. All domain logic remains independent from storage, parsers, and LLM providers. Every subsystem is first proven with fake adapters before integrating real implementations.

## Phases

- [x] **Phase 1: Compiler Foundation** - Domain model, ports, CompilerContext, and pass-registry mechanics exist and are proven in isolation with fake passes, with zero LLM/filesystem/YAML imports in domain code (completed 2026-06-30)
- [ ] **Phase 2: Document Compiler** - Markdown sources compile into Document IR end-to-end, through deterministic passes and one LLM-backed extraction pass, with a fake adapter proving LLMPort is swappable

## Phase Details

### Phase 1: Compiler Foundation

**Goal**: The domain model, ports, CompilerContext, and pass-registry mechanics exist and are proven correct in isolation — before any real pass, parser, or LLM adapter is written.
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, CORE-07, PASS-01, PASS-02, PASS-03, PASS-04, PASS-05, EXT-01, STOR-01, STOR-02 (see REQUIREMENTS.md for full text and concrete sub-deliverables: Pass Registry, Pipeline, Diagnostics model, Dependency Graph, Artifact Manifest, Cache abstraction)
**Success Criteria** (what must be TRUE):

  1. Domain modules (Concept, Relation, Taxonomy, Document entities; ConceptId, RelationId, Checksum, SourceRef value objects) import successfully with zero dependency on any LLM SDK, filesystem library, or YAML library
  2. A developer can write and register a new trivial CompilerPass (consuming one fake IR, producing another) without editing any existing pass or core pipeline file, and the pipeline executes it in the correct order purely from its declared dependencies
  3. Running the same set of fake passes twice against the same fake inputs produces byte-identical output artifacts, and each pass's output includes structured diagnostics (errors/warnings/infos) rather than printed/logged side effects
  4. A fake LLMPort, fake RepositoryPort, and fake MarkdownParserPort each satisfy their respective port contracts and can be swapped in CompilerContext without any domain or pass code change
  5. Writing a fake artifact through the repository port produces one individual YAML file per artifact (no monolithic JSON), in a directory that is verifiably separate from any raw-source directory

**Plans:** 4/4 plans complete
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Scaffold uv project (pyproject.toml, src/kir 5-package skeleton, pytest baseline)
- [x] 01-02-PLAN.md — Domain models, value objects, and ports (CORE-01, CORE-06, CORE-07)
- [x] 01-03-PLAN.md — Pass registry, CompilerContext, version constants (CORE-02..05, PASS-02, PASS-05, EXT-01)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-04-PLAN.md — Fakes, YAML repository adapter, end-to-end proofs (CORE-02, CORE-04, CORE-06, PASS-01, PASS-03, PASS-04, STOR-01, STOR-02)

### Phase 2: Document Compiler

**Goal**: A single Markdown source compiles deterministically into a self-contained Document IR, including LLM-backed concept/glossary/entity/reference extraction, without merging information across documents.
**Depends on**: Phase 1
**Requirements**: DOC-01, DOC-02, DOC-03, LLM-01, LLM-02, LLM-03 (see REQUIREMENTS.md for full text and concrete sub-deliverables: Structured Output, Prompt Registry, Prompt Versioning, Provider Adapter, Caching, Replay Tests)
**Success Criteria** (what must be TRUE):

  1. Given a single Markdown file, the Document Compiler produces a Document IR containing id, title, source, checksum, language, sections, concepts, glossary, entities, and references
  2. Compiling two different Markdown files independently never causes either resulting Document IR to contain information from the other document
  3. The concept/glossary/entity/reference extraction pass depends only on LLMPort and returns a validated structured (Pydantic) output; a fake LLM adapter and a real provider-backed adapter both satisfy LLMPort and are swappable without touching pass code
  4. Re-running the extraction pass against an unchanged document (same checksum, prompt version, schema version, pinned model id) reproduces the identical cached output without re-calling the LLM
  5. The extraction pass's unit tests run entirely against recorded/mocked LLM responses (golden fixtures), with zero live API calls made during the test suite

**Plans:** 1/5 plans executed
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Contracts and test infrastructure: narrow LLMPort/MarkdownParserPort, add Document.diagnostics, extend CompilerContext, install deps, wire asyncio_mode + ALLOW_MODEL_REQUESTS guard (DOC-01, DOC-03, LLM-01, LLM-02, LLM-03)

**Wave 2** *(parallel — no file overlap)*

- [ ] 02-02-PLAN.md — LLM infrastructure package: PydanticAIAdapter, FakeLLMAdapter, LLMCache, InMemoryCache, PromptRegistry, extract_v1.md prompt, LLM unit tests (LLM-01, LLM-02, LLM-03)
- [ ] 02-03-PLAN.md — Deterministic passes: MarkdownItAdapter, ParsePass, SectionPass, MetadataPass, document_registry, pass unit tests (DOC-01, DOC-02)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 02-04-PLAN.md — ExtractConceptsPass (async, D-03 failure, cache), DocumentCompiler service, 10 golden fixtures, extraction + integration tests (DOC-01, DOC-02, DOC-03, LLM-01, LLM-02, LLM-03)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Compiler Foundation | 4/4 | Complete    | 2026-06-30 |
| 2. Document Compiler | 1/5 | In Progress|  |
