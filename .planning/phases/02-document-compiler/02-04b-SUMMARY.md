---
phase: 02-document-compiler
plan: "04b"
subsystem: document-compiler
tags: [golden-fixtures, extract-concepts, fake-llm, cache-hit, diagnostics, document-ir]

# Dependency graph
requires:
  - phase: 02-02
    provides: FakeLLMAdapter, LLMCache, InMemoryCache, PromptRegistry
  - phase: 02-03
    provides: ParsePass, SectionPass, MetadataPass, document_registry
  - phase: 02-04a
    provides: ExtractConceptsPass, DocumentCompiler, D-03 failure path

provides:
  - "10 hand-authored golden fixture Markdown files (doc_01–doc_10) in tests/compiler/documents/fixtures/extract_concepts/"
  - "expected_outputs.py: DOC_01_EXPECTED through DOC_10_EXPECTED as DocumentExtractionOutput constants"
  - "test_extract_concepts_pass.py: cache hit (LLM-02), D-03 failure diagnostic, golden fixture replay for doc_01 and doc_07"
  - "test_document_compiler.py: DOC-01 full IR, DOC-02 no cross-contamination, pipeline length == 4"
  - "tests/compiler/documents/conftest.py: make_phase2_context() helper for Phase 2 test setup"

affects:
  - 02-05

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Golden fixture replay: FakeLLMAdapter(output=DOCXX_EXPECTED) replays hand-crafted outputs without live LLM calls"
    - "Cache hit test: same IR + same context → call_count stays 1 after two extract_concepts_pass calls"
    - "D-03 test: _ErrorFakeLLMAdapter raises on extract(), assert Diagnostic appended, function returns"
    - "Cross-contamination test: separate compiler instances per file, assert section content sets are disjoint"

key-files:
  created:
    - tests/compiler/documents/fixtures/extract_concepts/doc_01_rich.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_02_glossary_heavy.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_03_entity_reference.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_04_category_boundary.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_05_implicit_terminology.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_06_implicit_terminology_2.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_07_genuinely_sparse.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_08_world_knowledge_adjacent.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_09_mixed_headings.md
    - tests/compiler/documents/fixtures/extract_concepts/doc_10_rich_2.md
    - tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py
    - tests/compiler/documents/test_extract_concepts_pass.py
    - tests/compiler/documents/test_document_compiler.py
    - tests/compiler/documents/conftest.py
  modified: []

key-decisions:
  - "make_phase2_context() helper lives in conftest.py (not a fixture) so tests can construct multiple independent contexts per test"
  - "_ErrorFakeLLMAdapter defined in conftest.py alongside make_phase2_context() — keeps error-raising logic out of the FakeLLMAdapter that ships in src/"
  - "test_no_cross_contamination uses separate DocumentCompiler instances per file (separate caches) to prevent shared cache from masking isolation bugs"
  - "DOC_02_EXPECTED uses empty concepts list — glossary-heavy fixture has no standalone concepts since all terms are explicitly defined"

patterns-established:
  - "Phase 2 context helper: make_phase2_context(fake_output=X, raise_error=E) builds full CompilerContext for extraction tests"
  - "Golden fixture replay: FakeLLMAdapter configured with hand-crafted expected output, asserts IR fields match extracted DTO names"
  - "Cache hit test: single shared LLMCache across two pass calls on same IR; assert adapter.call_count stays 1"

requirements-completed: [DOC-01, DOC-02, DOC-03, LLM-02, LLM-03]

# Metrics
duration: 5min
completed: 2026-07-01
---

# Phase 02 Plan 04b: Golden Fixtures and Extraction Test Suite Summary

**10 hand-authored Zephyr-domain golden fixtures with DocumentExtractionOutput constants, extraction pass unit tests (cache hit, D-03 failure, fixture replay), and DocumentCompiler integration tests (full IR, no cross-contamination)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-01T07:22:27Z
- **Completed:** 2026-07-01T07:27:43Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments

- Created 10 synthetic Markdown fixtures (Zephyr framework domain) covering all composition types from AI-SPEC.md Section 5: 2 rich, 1 glossary-heavy, 1 entity-reference-heavy, 1 category-boundary, 2 implicit-terminology, 1 genuinely sparse, 1 world-knowledge-adjacent, 1 mixed-headings (H1–H4)
- `expected_outputs.py` defines `DOC_01_EXPECTED` through `DOC_10_EXPECTED` as fully-specified `DocumentExtractionOutput` constants; `DOC_07_EXPECTED` has exactly 1 concept and empty glossary/entities/references
- `test_extract_concepts_pass.py`: 5 tests covering LLM call, LLM-02 cache hit (call_count stays 1 on second call), D-03 failure diagnostic (no halt), golden fixture replay for doc_01 and doc_07
- `test_document_compiler.py`: 3 tests covering DOC-01 full IR (id, title, 64-char checksum, language, sections, concepts), DOC-02 no cross-contamination (separate section content sets), and pipeline length == 4
- All 121 tests pass with zero live API calls (`ALLOW_MODEL_REQUESTS=False` guard remains active)

## Task Commits

1. **Task 1: Golden fixture corpus (D-04) — 10 synthetic Markdown fixtures and expected_outputs.py** - `98ecf47` (feat)
2. **Task 2: Extraction pass unit tests and DocumentCompiler integration tests** - `3da5924` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `tests/compiler/documents/fixtures/__init__.py` — package init
- `tests/compiler/documents/fixtures/extract_concepts/__init__.py` — package init
- `tests/compiler/documents/fixtures/extract_concepts/doc_01_rich.md` — rich Zephyr doc with all four categories
- `tests/compiler/documents/fixtures/extract_concepts/doc_02_glossary_heavy.md` — 5 explicit definitions, no entities/refs
- `tests/compiler/documents/fixtures/extract_concepts/doc_03_entity_reference.md` — 6 entities, 3 references, no glossary/concepts
- `tests/compiler/documents/fixtures/extract_concepts/doc_04_category_boundary.md` — "channel" is glossary (not concept), registry as entity
- `tests/compiler/documents/fixtures/extract_concepts/doc_05_implicit_terminology.md` — backpressure/throttling concepts never explicitly defined
- `tests/compiler/documents/fixtures/extract_concepts/doc_06_implicit_terminology_2.md` — schema evolution concepts never explicitly defined
- `tests/compiler/documents/fixtures/extract_concepts/doc_07_genuinely_sparse.md` — one concept, no other categories
- `tests/compiler/documents/fixtures/extract_concepts/doc_08_world_knowledge_adjacent.md` — "cache" redefined in Zephyr-specific way
- `tests/compiler/documents/fixtures/extract_concepts/doc_09_mixed_headings.md` — H1/H2/H3/H4 structure, plugin concepts
- `tests/compiler/documents/fixtures/extract_concepts/doc_10_rich_2.md` — second rich fixture on configuration/settings topic
- `tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py` — DOC_01_EXPECTED through DOC_10_EXPECTED
- `tests/compiler/documents/conftest.py` — make_phase2_context() helper and _ErrorFakeLLMAdapter
- `tests/compiler/documents/test_extract_concepts_pass.py` — 5 unit tests for extract_concepts_pass
- `tests/compiler/documents/test_document_compiler.py` — 3 integration tests for DocumentCompiler

## Decisions Made

- `make_phase2_context()` implemented as a plain function (not a pytest fixture) so individual tests can create multiple independent contexts within a single test (e.g., `test_no_cross_contamination` needs two separate compiler+cache pairs)
- `_ErrorFakeLLMAdapter` is a local class in `conftest.py` — keeps error-injection concern out of `FakeLLMAdapter` in `src/` and avoids modifying the production-tree fake
- `test_no_cross_contamination` uses fresh `DocumentCompiler` instances per file (not a shared compiler) to ensure each compilation starts with a clean LLM cache — a shared cache could return the same cached output for both files if they happened to share a checksum (impossible here but defended against by design)
- `DOC_02_EXPECTED` has an empty `concepts` list — all five terms in doc_02 are explicitly defined (glossary), so none should appear as standalone concepts per the AI-SPEC.md category-boundary rule (glossary and concept are mutually exclusive for the same term)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `DocumentCompiler.compile(path)` is now fully tested end-to-end with real passes + FakeLLMAdapter
- Golden fixture corpus (D-04) provides a ready-made test harness for Phase 3 (Knowledge Compiler) integration tests
- All LLM-02, LLM-03, DOC-01, DOC-02, DOC-03 requirements are now proven with automated tests
- Phase 02 is complete — all 5 plans (02-01 through 02-04b) are executed and all tests green

## Known Stubs

None — all DocumentExtractionOutput constants are fully specified with real content from the fixture files.

## Threat Flags

None — all tests use FakeLLMAdapter and `ALLOW_MODEL_REQUESTS=False` remains active. No new network endpoints or trust-boundary violations introduced.

## Self-Check: PASSED

- [x] `tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py` exists
- [x] `tests/compiler/documents/test_extract_concepts_pass.py` exists
- [x] `tests/compiler/documents/test_document_compiler.py` exists
- [x] `tests/compiler/documents/conftest.py` exists
- [x] Commit `98ecf47` (Task 1) exists in git log
- [x] Commit `3da5924` (Task 2) exists in git log
- [x] `uv run pytest tests/compiler/documents/ -x -q` — 34 passed
- [x] `uv run pytest -x -q` — 121 passed, zero failures

---

*Phase: 02-document-compiler*
*Completed: 2026-07-01*
