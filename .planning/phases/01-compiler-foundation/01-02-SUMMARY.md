---
phase: 01-compiler-foundation
plan: 02
subsystem: core
tags: [pydantic, domain-model, ports, hexagonal-architecture, immutability]

# Dependency graph
requires: ["01-01"]
provides:
  - "Frozen, extra=forbid Pydantic value objects: ConceptId, RelationId, Checksum (value_objects.py), SourceRef (models/provenance.py)"
  - "Diagnostic + Severity enum (CORE-06) for structured pass-level diagnostics"
  - "Six domain entity/value-object models: Document+Section, Concept, Relation, Taxonomy, Conflict — all frozen, extra=forbid, tuple-not-list accumulating fields"
  - "ArtifactManifest scoped to artifact_id+version only (D-04)"
  - "FakeIR — minimal Pydantic model decoupled from Document/Concept, reserved for Plan 03/04 pass-mechanics tests"
  - "Four typing.Protocol ports: LLMPort, RepositoryPort, MarkdownParserPort, CachePort — structural typing, no inheritance required"
  - "CORE-01 AST-based import-boundary audit (tests/core/test_import_boundaries.py), manually verified to catch a forbidden import"
affects: ["01-03", "01-04", "phase-02"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "model_config = ConfigDict(frozen=True, extra=\"forbid\") on every domain/IR model — CORE-07 + ASVS V5"
    - "tuple[...] (never list[...]) for all accumulating fields — list fields stay mutable via .append() even when frozen=True"
    - "Distinct ConceptId/RelationId wrapper types (not bare str aliases) so the two value-object IDs can never be silently interchanged"
    - "SourceRef's single canonical home is models/provenance.py — value_objects.py imports it rather than redefining it"
    - "typing.Protocol ports with method-signature-only bodies; verified via Protocol in __mro__ + TypeError on direct instantiation, not @runtime_checkable + isinstance"
    - "AST-based (not regex/grep) import-boundary audit to catch aliased/dynamic imports reliably"

key-files:
  created:
    - src/kir/core/domain/value_objects.py
    - src/kir/core/domain/models/provenance.py
    - src/kir/core/domain/models/diagnostic.py
    - src/kir/core/domain/models/document.py
    - src/kir/core/domain/models/concept.py
    - src/kir/core/domain/models/relation.py
    - src/kir/core/domain/models/taxonomy.py
    - src/kir/core/domain/models/conflict.py
    - src/kir/core/domain/manifest.py
    - src/kir/core/domain/ir.py
    - src/kir/core/ports/llm_port.py
    - src/kir/core/ports/repository_port.py
    - src/kir/core/ports/parser_port.py
    - src/kir/core/ports/cache_port.py
    - tests/core/domain/test_value_objects.py
    - tests/core/domain/test_diagnostic.py
    - tests/core/domain/test_document.py
    - tests/core/domain/test_concept.py
    - tests/core/domain/test_relation.py
    - tests/core/domain/test_taxonomy.py
    - tests/core/domain/test_conflict.py
    - tests/core/domain/test_manifest.py
    - tests/core/domain/test_immutability.py
    - tests/core/test_import_boundaries.py
  modified: []

key-decisions:
  - "SourceRef's canonical home is src/kir/core/domain/models/provenance.py, not value_objects.py — value_objects.py imports it instead of redefining it, per the plan's explicit 'pick ONE file' instruction."
  - "Relation.relation_type stays a plain str, not an enum — relation vocabulary is core-and-extensible per PROJECT.md's Architectural Decisions, finalized in Phase 3/M2."
  - "Document.concepts/glossary/entities/references use tuple[str, ...] placeholder element types — real typed references are a Phase 2 concern once extraction passes exist."
  - "ArtifactManifest has exactly two fields (artifact_id, version) — no checksum/dependency-index field, per D-04 scope limit."
  - "Protocol ports verified via 'Protocol in __mro__' + TypeError-on-direct-instantiation, not @runtime_checkable + isinstance, per RESEARCH.md's anti-pattern guidance."

requirements-completed: ["CORE-01", "CORE-06", "CORE-07"]

# Metrics
duration: 25min
completed: 2026-06-30
---

# Phase 1 Plan 2: Domain Model and Ports Summary

**Frozen, extra=forbid Pydantic domain model (Document/Concept/Relation/Taxonomy/Conflict/Diagnostic/ArtifactManifest/value objects) plus four typing.Protocol ports, with an automated AST-based audit proving zero forbidden imports in the domain layer**

## Performance

- **Duration:** 25 min
- **Started:** 2026-06-30T05:12:00Z
- **Completed:** 2026-06-30T05:37:00Z
- **Tasks:** 3
- **Files modified:** 23 (23 created, 0 modified)

## Accomplishments
- All value objects (`ConceptId`, `RelationId`, `Checksum`, `SourceRef`) construct, are frozen (reject field reassignment), and reject unknown fields (`extra="forbid"`); `Checksum` and `SourceRef` are equality-comparable and hashable
- `Diagnostic` + `Severity` enum (exactly `ERROR`/`WARNING`/`INFO`) implement CORE-06's structured diagnostic contract
- All four ports (`LLMPort`, `RepositoryPort`, `MarkdownParserPort`, `CachePort`) are real `typing.Protocol` classes — importable, structurally distinct, and cannot be instantiated directly
- Full entity/value-object set (`Document`+`Section`, `Concept`, `Relation`, `Taxonomy`, `Conflict`) constructs with the exact field lists specified by DOC-01 and the plan, all frozen + extra-forbidden, all accumulating fields stored as `tuple`
- `ArtifactManifest` scoped to exactly `artifact_id` + `version` per D-04; verified via an explicit `model_fields.keys()` assertion
- `FakeIR` exists as a minimal, Document/Concept-decoupled model reserved for later pass-mechanics tests
- CORE-07 immutability proven across Document, Concept, and FakeIR: `model_copy(update=...)` produces a new instance leaving the original unchanged, and direct field reassignment raises `ValidationError`
- CORE-01 import-boundary audit (`tests/core/test_import_boundaries.py`) passes against the real `src/kir/core/domain/` tree; manually verified red by temporarily adding `import yaml` to `manifest.py`, confirming the test failed, then reverting before commit
- Full test suite: 45 tests pass (`uv run pytest -q`), exit code 0

## Task Commits

Each task was committed atomically:

1. **Task 1: Value objects, Diagnostic, and structural contracts (Protocol ports)** - `250e0fc` (feat)
2. **Task 2: Entity models, ArtifactManifest, FakeIR, and immutability proofs** - `2854ce8` (feat)
3. **Task 3: CORE-01 import-boundary audit test** - `8c8d30f` (test)

**Plan metadata:** (final commit pending below)

## Files Created/Modified
- `src/kir/core/domain/value_objects.py` - `ConceptId`, `RelationId`, `Checksum` frozen value objects
- `src/kir/core/domain/models/provenance.py` - `SourceRef` (canonical home)
- `src/kir/core/domain/models/diagnostic.py` - `Diagnostic`, `Severity` enum (CORE-06)
- `src/kir/core/domain/models/document.py` - `Document`, `Section` (DOC-01 field list)
- `src/kir/core/domain/models/concept.py` - `Concept` entity
- `src/kir/core/domain/models/relation.py` - `Relation` value object (plain-string `relation_type`)
- `src/kir/core/domain/models/taxonomy.py` - `Taxonomy` value object (minimal, M2 scope deferred)
- `src/kir/core/domain/models/conflict.py` - `Conflict` value object (minimal, M2 scope deferred)
- `src/kir/core/domain/manifest.py` - `ArtifactManifest` (artifact_id + version only, D-04)
- `src/kir/core/domain/ir.py` - `FakeIR` for Plan 03/04 pass-mechanics tests
- `src/kir/core/ports/llm_port.py` - `LLMPort` Protocol
- `src/kir/core/ports/repository_port.py` - `RepositoryPort` Protocol (`save`/`load`)
- `src/kir/core/ports/parser_port.py` - `MarkdownParserPort` Protocol (`parse`)
- `src/kir/core/ports/cache_port.py` - `CachePort` Protocol (`get`/`set`, generic KV only per D-03)
- `tests/core/domain/test_value_objects.py`, `test_diagnostic.py`, `test_document.py`, `test_concept.py`, `test_relation.py`, `test_taxonomy.py`, `test_conflict.py`, `test_manifest.py`, `test_immutability.py` - construction/invariant/immutability suites (43 tests)
- `tests/core/test_import_boundaries.py` - CORE-01 AST-based forbidden-import audit (2 tests)

## Decisions Made
- `SourceRef`'s single canonical home is `models/provenance.py`; `value_objects.py` does not redefine it
- `Relation.relation_type` stays `str`, not an enum — vocabulary is core-and-extensible (Phase 3/M2 concern)
- `Document`'s `concepts`/`glossary`/`entities`/`references` fields use `tuple[str, ...]` placeholders, with a code comment noting Phase 2 will replace these with typed references
- `ArtifactManifest` has exactly two fields per D-04 — verified by an explicit field-set assertion test
- Port-Protocol verification uses `Protocol in __mro__` + direct-instantiation `TypeError`, not `@runtime_checkable`/`isinstance`, matching RESEARCH.md's anti-pattern guidance

## Deviations from Plan

None - plan executed exactly as written. All file paths, field lists, and scope limits (D-03, D-04) from the plan were followed verbatim.

## Issues Encountered

None.

## User Setup Required

None - pure domain-model/ports code, no external service configuration required.

## Next Phase Readiness
- Every entity/value-object/port type listed in CORE-01 now exists, is importable, and is proven frozen + extra-forbidding + import-boundary-clean
- Plan 03 (pass registry mechanics) and Plan 04 (test fixtures/conftest) can now import `FakeIR`, `Diagnostic`, and the four ports without any further domain-model setup
- Phase 2's real Document IR assembly can construct real `Document`/`Section`/`Concept` instances against this exact schema — only the placeholder `tuple[str, ...]` fields on `Document` (concepts/glossary/entities/references) and `Relation`'s vocabulary will need real typed replacements, both already flagged as Phase 2/3 follow-ups in code comments
- No blockers

---
*Phase: 01-compiler-foundation*
*Completed: 2026-06-30*
