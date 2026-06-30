---
phase: 02-document-compiler
plan: "04b"
type: execute
wave: 4
depends_on:
  - 02-04a
  - 02-02
  - 02-03
files_modified:
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
autonomous: true
requirements:
  - DOC-01
  - DOC-02
  - DOC-03
  - LLM-02
  - LLM-03

must_haves:
  truths:
    - "All 10 golden fixture synthetic Markdown files exist under tests/compiler/documents/fixtures/extract_concepts/"
    - "On cache hit, ExtractConceptsPass returns the cached DocumentExtractionOutput without calling ctx.llm.extract() — FakeLLMAdapter.call_count stays 0 on second call"
    - "On LLM extraction failure (FakeLLMAdapter raises), the Document IR still has a Diagnostic with code='extraction-failed' and concepts/glossary/entities/references remain empty — pipeline does not halt"
    - "Compiling two different Markdown files independently never causes either Document IR to contain sections from the other file (DOC-02 isolation)"
    - "uv run pytest tests/compiler/documents/ -x -q passes (all extraction pass and document compiler tests green; zero live API calls)"
  artifacts:
    - path: "tests/compiler/documents/fixtures/extract_concepts/"
      provides: "10 hand-authored synthetic Markdown fixtures + expected outputs (D-04)"
    - path: "tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py"
      provides: "DOC_01_EXPECTED through DOC_10_EXPECTED as DocumentExtractionOutput constants"
      contains: "DOC_01_EXPECTED"
    - path: "tests/compiler/documents/test_extract_concepts_pass.py"
      provides: "Unit tests for cache hit, D-03 failure, golden fixture replay"
      contains: "test_extraction_failure_produces_diagnostic_not_halt"
    - path: "tests/compiler/documents/test_document_compiler.py"
      provides: "Integration tests for DOC-01 full IR and DOC-02 no cross-contamination"
      contains: "test_no_cross_contamination"
  key_links:
    - from: "tests/compiler/documents/test_extract_concepts_pass.py"
      to: "src/kir/compiler/documents/passes/extract_concepts.py"
      via: "imports extract_concepts_pass directly"
      pattern: "from kir.compiler.documents.passes.extract_concepts import"
    - from: "tests/compiler/documents/test_document_compiler.py"
      to: "src/kir/compiler/documents/compiler.py"
      via: "imports DocumentCompiler and calls compile()"
      pattern: "from kir.compiler.documents.compiler import DocumentCompiler"
---

<objective>
Create the golden fixture corpus (D-04: 10 synthetic Markdown files + expected_outputs.py) and the full test suite (test_extract_concepts_pass.py + test_document_compiler.py) that prove ExtractConceptsPass and DocumentCompiler behave correctly under cache hits, LLM failures, fixture replay, and cross-document isolation.

Purpose: Delivers LLM-03 (all extraction tests use FakeLLMAdapter with zero live API calls), LLM-02 (cache hit test), D-03 failure handling proof, and DOC-02 isolation proof at integration level.

Output: 10 golden fixture .md files, expected_outputs.py with 10 DocumentExtractionOutput constants, full unit and integration test suite — all green with zero live API calls.
</objective>

<execution_context>
@/Users/mniedre/.claude/gsd-core/workflows/execute-plan.md
@/Users/mniedre/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-document-compiler/02-CONTEXT.md
@.planning/phases/02-document-compiler/02-RESEARCH.md
@.planning/phases/02-document-compiler/02-AI-SPEC.md
@.planning/phases/02-document-compiler/02-04a-SUMMARY.md
@.planning/phases/02-document-compiler/02-02-SUMMARY.md
@.planning/phases/02-document-compiler/02-03-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Golden fixture corpus (D-04) — 10 synthetic Markdown files and expected_outputs.py</name>
  <files>
    tests/compiler/documents/fixtures/extract_concepts/doc_01_rich.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_02_glossary_heavy.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_03_entity_reference.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_04_category_boundary.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_05_implicit_terminology.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_06_implicit_terminology_2.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_07_genuinely_sparse.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_08_world_knowledge_adjacent.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_09_mixed_headings.md,
    tests/compiler/documents/fixtures/extract_concepts/doc_10_rich_2.md,
    tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py
  </files>
  <read_first>
    - src/kir/llm/pydantic_ai_adapter.py (DocumentExtractionOutput and DTO classes — used to build expected outputs)
    - .planning/phases/02-document-compiler/02-AI-SPEC.md Section 5 (reference dataset composition: 2-3 rich, 2 category-boundary, 2 implicit-terminology, 1 sparse, 1 world-knowledge-adjacent, 1-2 mixed-headings)
    - .planning/phases/02-document-compiler/02-CONTEXT.md D-04 (hand-authored synthetic Markdown, hand-crafted expected output pairs)
  </read_first>
  <action>
Create the 10 golden fixture Markdown documents per D-04 and AI-SPEC.md Section 5's composition guide. These are hand-authored synthetic documents (not real project excerpts), each 2-5 sections, clearly constrained so the expected extraction is unambiguous. Content is about a fictional "Zephyr" framework — neutral domain that avoids leaking real-world knowledge.

Fixture composition (one file each):
- doc_01_rich.md: Rich doc with all four categories clearly present — 3 sections, 2-3 concepts, 2 glossary terms (explicitly defined), 1-2 entities (named organizations/systems), 1 reference (external URL or doc link).
- doc_02_glossary_heavy.md: Primarily glossary terms — 3 sections with multiple "X is defined as Y" sentences. Fewer concepts, no entities, no references.
- doc_03_entity_reference.md: Entity and reference heavy — 2-3 sections mentioning named people, organizations, systems, and links to external resources. Minimal concepts, no glossary.
- doc_04_category_boundary.md: Deliberately ambiguous — a term that is both used-as-a-concept and explicitly-defined (should be glossary), and an organization reference that could be entity or reference. Tests category-correctness behavior.
- doc_05_implicit_terminology.md: A term used repeatedly but never given an explicit "X is defined as Y" sentence — tests recall on implicit/undefined-but-used terminology (AI-SPEC.md failure mode).
- doc_06_implicit_terminology_2.md: A second implicit-terminology fixture with different phrasing patterns.
- doc_07_genuinely_sparse.md: Very short — one section, 2-3 sentences, one extractable concept, no glossary, no entities, no references. Tests "correctly sparse" vs silent under-extraction.
- doc_08_world_knowledge_adjacent.md: Redefines a well-known term ("cache") in a project-specific way that differs from the common definition. Expected output must use the document's narrow definition, not the textbook one.
- doc_09_mixed_headings.md: Multiple heading levels (H1, H2, H3, H4) in the same document — tests extraction across irregular section structure per D-01.
- doc_10_rich_2.md: Second rich fixture with a different topic (configuration and settings) — confirms extraction generalizes.

Create tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py:
- Import DocumentExtractionOutput, ExtractedConceptDTO, ExtractedGlossaryTermDTO, ExtractedEntityDTO, ExtractedReferenceDTO from kir.llm.pydantic_ai_adapter.
- Define one named constant per fixture: DOC_01_EXPECTED = DocumentExtractionOutput(concepts=[...], glossary=[...], entities=[...], references=[...]) through DOC_10_EXPECTED.
- Each constant is a fully-specified hand-crafted expected output matching the corresponding .md file's content.
- DOC_07_EXPECTED (sparse) is intentionally minimal: one concept, empty glossary/entities/references.
  </action>
  <verify>
    <automated>ls tests/compiler/documents/fixtures/extract_concepts/*.md | wc -l && python -c "from tests.compiler.documents.fixtures.extract_concepts.expected_outputs import DOC_01_EXPECTED, DOC_07_EXPECTED, DOC_10_EXPECTED; print('ok')"</automated>
  </verify>
  <done>All 10 fixture .md files exist with non-empty content. expected_outputs.py defines DOC_01_EXPECTED through DOC_10_EXPECTED as importable DocumentExtractionOutput instances. DOC_07_EXPECTED has exactly one concept and empty glossary/entities/references.</done>
</task>

<task type="auto">
  <name>Task 2: Extraction pass unit tests and DocumentCompiler integration tests</name>
  <files>
    tests/compiler/documents/test_extract_concepts_pass.py,
    tests/compiler/documents/test_document_compiler.py
  </files>
  <read_first>
    - src/kir/compiler/documents/passes/extract_concepts.py (the pass under test — created in 02-04a)
    - src/kir/compiler/documents/compiler.py (DocumentCompiler service — created in 02-04a)
    - src/kir/llm/fake_adapter.py (FakeLLMAdapter — used for all extraction tests; no live LLM)
    - src/kir/llm/cache.py (LLMCache, InMemoryCache — used in cache hit/miss tests)
    - src/kir/llm/prompts/registry.py (PromptRegistry — used in test context construction)
    - src/kir/core/domain/models/document.py (Document, Section — for test IR construction)
    - src/kir/core/domain/value_objects.py (Checksum — for test IR construction)
    - src/kir/core/passes/context.py (CompilerContext — must include llm_cache, prompts, prompt_version for Phase 2 tests)
    - src/kir/core/config/versions.py (prompt_version, schema_version, compiler_version constants)
    - tests/conftest.py (fake_compiler_context — may need a Phase 2 version with llm_cache and prompts wired)
    - tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py (DOC_01_EXPECTED, DOC_07_EXPECTED — just created in Task 1)
    - .planning/phases/02-document-compiler/02-VALIDATION.md (per-task test map)
  </read_first>
  <action>
Create tests/compiler/documents/test_extract_concepts_pass.py. All async tests use asyncio_mode=auto (no @pytest.mark.asyncio needed). Define a module-level helper make_doc_context(fake_output=None, raise_error=None) that builds a CompilerContext with FakeLLMAdapter configured per the parameters, LLMCache(InMemoryCache()), PromptRegistry(), prompt_version="1", schema_version="1", and compiler_version from kir.core.config.versions. Alternatively add a fixture to tests/compiler/documents/conftest.py (create this file if it does not exist) — avoid duplicating construction boilerplate in every test.

Tests to implement:
- test_extract_concepts_pass_calls_llm_and_populates_document: Create a Document with one section, call extract_concepts_pass(ir, ctx_with_fake_llm configured with DOC_01_EXPECTED), assert FakeLLMAdapter.call_count == 1 and result.concepts is not empty.
- test_extract_concepts_pass_cache_hit_skips_llm_call (LLM-02): Prime the cache manually with a stored DocumentExtractionOutput, call extract_concepts_pass twice on the same document, confirm llm.call_count == 1 after first call (cache miss triggers LLM) and still 1 after second call (cache hit — no second LLM call).
- test_extraction_failure_produces_diagnostic_not_halt (D-03, LLM-03): Configure FakeLLMAdapter to raise RuntimeError("extraction failed"), call extract_concepts_pass, assert result has a Diagnostic with code="extraction-failed" and severity=ERROR; assert result.concepts == () and result.glossary == (); confirm the function returns rather than raises.
- test_extract_concepts_pass_with_golden_fixture_doc_01: Use FakeLLMAdapter(output=DOC_01_EXPECTED), run the pass on a Document seeded with doc_01_rich.md content, assert result.concepts == tuple(c.name for c in DOC_01_EXPECTED.concepts).
- test_extract_concepts_pass_with_golden_fixture_doc_07_sparse: Use FakeLLMAdapter(output=DOC_07_EXPECTED), run the pass, assert len(result.concepts) == 1 and result.glossary == ().

Create tests/compiler/documents/test_document_compiler.py. Requires tmp_path fixture for .md file I/O. All tests are async def (DocumentCompiler.compile() is async).

Tests to implement:
- test_document_compiler_compiles_markdown_to_full_document_ir (DOC-01): Write doc_01_rich.md text (read from the fixture file or inline a small equivalent) to tmp_path/doc.md, build DocumentCompiler with document_registry and a CompilerContext using MarkdownItAdapter, FakeLLMAdapter(output=DOC_01_EXPECTED), LLMCache(InMemoryCache()), PromptRegistry(). Await compiler.compile(tmp_path/"doc.md"). Assert result.id is non-empty, result.title is non-empty, result.checksum.value is a 64-char hex string, result.language == "en", len(result.sections) > 0, result.concepts is a tuple and len(result.concepts) > 0.
- test_no_cross_contamination (DOC-02): Write two different Markdown files (doc_a.md and doc_b.md) to tmp_path with different heading titles and section content. Compile each separately with fresh DocumentCompiler instances (fresh LLM cache each time — different FakeLLMAdapter per compile to return appropriately-labeled output). Assert: result_a.title != result_b.title, result_a.checksum.value != result_b.checksum.value, no section content in result_a.sections appears in result_b.sections and vice versa.
- test_document_compiler_pipeline_has_four_passes: Build DocumentCompiler(document_registry, ctx), access self._pipeline via the instance attribute, assert len(pipeline) == 4.
  </action>
  <verify>
    <automated>uv run pytest tests/compiler/documents/ -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>All extraction pass unit tests pass (cache hit, D-03 failure, golden fixture replay for doc_01 and doc_07). DocumentCompiler integration tests pass (DOC-01 full IR, DOC-02 no cross-contamination, pipeline length). Full test suite is green with zero live API calls.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| test fixtures → FakeLLMAdapter | All fixture-driven tests route through FakeLLMAdapter — no real API boundary is crossed |
| ALLOW_MODEL_REQUESTS guard → test suite | conftest.py autouse fixture blocks live API calls globally; any test escaping FakeLLMAdapter fails with a pydantic_ai error before hitting the network |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-12 | Information Disclosure | API credentials in test output or logs | mitigate | All tests use FakeLLMAdapter — no real credentials are loaded or logged. ALLOW_MODEL_REQUESTS=False autouse fixture ensures even a misconfigured test path cannot reach a live API. |
| T-02-SC | Tampering | npm/pip/cargo installs | mitigate | slopcheck + blocking human checkpoint for any [ASSUMED]/[SUS] packages |
</threat_model>

<verification>
After both tasks complete:
- uv run pytest tests/compiler/documents/ -x -q passes
- uv run pytest -x -q (full suite) passes with zero failures
- ls tests/compiler/documents/fixtures/extract_concepts/ shows 11 files (10 .md + expected_outputs.py)
- grep -c "ALLOW_MODEL_REQUESTS" tests/conftest.py returns 1 (the guard remains active)
</verification>

<success_criteria>
All 10 golden fixture files exist with non-empty content. expected_outputs.py defines all 10 expected output constants. All extraction pass unit tests pass (cache hit, D-03 failure, golden fixture replay). DocumentCompiler integration tests pass (full IR, no cross-contamination). Full test suite green with zero live API calls.
</success_criteria>

<output>
Create .planning/phases/02-document-compiler/02-04b-SUMMARY.md when done.
</output>
