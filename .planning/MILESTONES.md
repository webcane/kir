# Milestones

## v1.0 M1 - Deterministic Document Compiler (Shipped: 2026-07-01)

**Phases completed:** 3 phases, 10 plans, 22 tasks

**Key accomplishments:**

- uv-managed Python 3.13 kir project with pydantic 2.13.4 + pytest 9.1.1, src-layout core/tooling package skeleton, and a working `uv run pytest` zero-test baseline (exit 0)
- Frozen, extra=forbid Pydantic domain model (Document/Concept/Relation/Taxonomy/Conflict/Diagnostic/ArtifactManifest/value objects) plus four typing.Protocol ports, with an automated AST-based audit proving zero forbidden imports in the domain layer
- graphlib.TopologicalSorter-based PassRegistry closing ARCHITECTURE.md's comment-only `pipeline()` gap, plus an immutable, explicitly-constructed CompilerContext DI container — both proven via TDD RED/GREEN with a literal EXT-01 no-edit-existing-files proof
- Fake LLMPort/RepositoryPort(x2)/MarkdownParserPort/CachePort implementations plus a real ruamel.yaml-backed YamlFileRepository adapter, proving Phase 1's byte-identical-rerun, diagnostics-accumulation, and port-substitutability success criteria via shared contract tests
- One-liner:
- One-liner:
- Async LLM-backed extraction pass with four-part cache key (LLM-02), D-03 diagnostic failure path, and DocumentCompiler service wiring all four passes into a runnable pipeline
- 10 hand-authored Zephyr-domain golden fixtures with DocumentExtractionOutput constants, extraction pass unit tests (cache hit, D-03 failure, fixture replay), and DocumentCompiler integration tests (full IR, no cross-contamination)
- DocumentCompiler.compile() now persists Document IR to RepositoryPort via ir.model_dump() after the pipeline loop, closing the STOR-01/STOR-02 gap with a one-line change and two targeted test assertions

---
