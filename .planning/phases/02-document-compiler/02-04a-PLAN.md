---
phase: 02-document-compiler
plan: "04a"
type: execute
wave: 3
depends_on:
  - 02-02
  - 02-03
files_modified:
  - src/kir/compiler/documents/passes/extract_concepts.py
  - src/kir/compiler/documents/passes/__init__.py
  - src/kir/compiler/documents/compiler.py
autonomous: true
requirements:
  - DOC-01
  - DOC-02
  - DOC-03
  - LLM-01
  - LLM-02
  - LLM-03

must_haves:
  truths:
    - "ExtractConceptsPass is async def, registered with depends_on=('parse', 'section', 'metadata'), and calls await ctx.llm.extract(sections=ir.sections, prompt=rendered_prompt)"
    - "On cache hit, ExtractConceptsPass returns the cached DocumentExtractionOutput without calling ctx.llm.extract() — FakeLLMAdapter.call_count stays 0"
    - "On LLM extraction failure (FakeLLMAdapter raises), the Document IR still has a Diagnostic with code='extraction-failed' and concepts/glossary/entities/references remain empty — pipeline does not halt"
    - "DocumentCompiler.compile(source_path) runs all four passes in dependency order and returns a fully-populated Document IR"
    - "document_registry.pipeline() returns all four passes including extract_concepts"
  artifacts:
    - path: "src/kir/compiler/documents/passes/extract_concepts.py"
      provides: "ExtractConceptsPass — async LLM-backed extraction pass"
      contains: "async def extract_concepts_pass"
    - path: "src/kir/compiler/documents/compiler.py"
      provides: "DocumentCompiler service wiring all four passes"
      contains: "class DocumentCompiler"
  key_links:
    - from: "src/kir/compiler/documents/passes/extract_concepts.py"
      to: "src/kir/core/ports/llm_port.py"
      via: "ctx.llm satisfies LLMPort — pass never imports PydanticAIAdapter directly"
      pattern: "ctx.llm.extract"
    - from: "src/kir/compiler/documents/passes/extract_concepts.py"
      to: "src/kir/llm/cache.py"
      via: "ctx.llm_cache is an LLMCache instance; pass calls ctx.llm_cache.get/set"
      pattern: "ctx.llm_cache.get"
    - from: "src/kir/compiler/documents/compiler.py"
      to: "src/kir/compiler/documents/passes/__init__.py"
      via: "DocumentCompiler receives document_registry; calls registry.pipeline()"
      pattern: "registry.pipeline"
---

<objective>
Implement ExtractConceptsPass (the async LLM-backed extraction pass, D-02/D-03) and DocumentCompiler (the service that wires all four passes into a runnable pipeline). This is the production-code half of Plan 04 — no fixtures or test files are created here; those follow in 02-04b.

Purpose: Delivers DOC-03 (structured LLM extraction via LLMPort seam), LLM-02 (cache hit suppresses re-extraction), and the DocumentCompiler service that proves all four passes wire together correctly.

Output: ExtractConceptsPass registered in the document pass registry, DocumentCompiler class with async compile() method, updated __init__.py forced import.
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
@.planning/phases/02-document-compiler/02-PATTERNS.md
@.planning/phases/02-document-compiler/02-02-SUMMARY.md
@.planning/phases/02-document-compiler/02-03-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: ExtractConceptsPass (async, D-03 failure handling, cache integration) and DocumentCompiler service</name>
  <files>
    src/kir/compiler/documents/passes/extract_concepts.py,
    src/kir/compiler/documents/passes/__init__.py,
    src/kir/compiler/documents/compiler.py
  </files>
  <read_first>
    - src/kir/compiler/documents/passes/__init__.py (document_registry and register_pass decorator — extract_concepts registers here; also must be added to forced import list)
    - src/kir/core/domain/models/document.py (Document fields — concepts/glossary/entities/references are still tuple[str, ...]; the pass populates them by converting ExtractedConceptDTO names to strings)
    - src/kir/core/domain/models/diagnostic.py (Diagnostic, Severity — used in D-03 failure path)
    - src/kir/core/passes/context.py (CompilerContext with llm, llm_cache, prompts, prompt_version, schema_version fields from Plan 01)
    - src/kir/llm/pydantic_ai_adapter.py (DocumentExtractionOutput shape — used to understand .concepts/.glossary/.entities/.references attributes in _apply_extraction helper)
    - src/kir/llm/cache.py (LLMCache.get/set interface — ctx.llm_cache is an LLMCache instance)
    - tests/core/passes/fakes/fake_passes.py (model_copy + diagnostics accumulation pattern)
    - .planning/phases/02-document-compiler/02-PATTERNS.md (extract_concepts.py and compiler.py sections)
    - .planning/phases/02-document-compiler/02-RESEARCH.md (Pattern 4 for ExtractConceptsPass, Pitfall 2 async requirement, Pitfall 3 forced import requirement, Anti-Patterns)
    - .planning/phases/02-document-compiler/02-AI-SPEC.md Section 4 (Implementation Guidance — async, D-03, cache hit/miss path)
  </read_first>
  <action>
Create src/kir/compiler/documents/passes/extract_concepts.py. This pass is ASYNC — the function signature is async def extract_concepts_pass(ir: Document, ctx: CompilerContext) -> Document:

The full logic:
1. Render the prompt: prompt = ctx.prompts.render("extract_v1", sections=ir.sections) — calls the PromptRegistry.render() method on ctx.prompts with the current document's sections.
2. Check cache: cached = ctx.llm_cache.get(checksum=ir.checksum.value, prompt_version=ctx.prompt_version, schema_version=ctx.schema_version, model_id=ctx.llm.model_id). If cached is not None, return _apply_extraction(ir, cached).
3. LLM call with D-03 failure handling:
   - try: result = await ctx.llm.extract(sections=list(ir.sections), prompt=prompt)
   - except Exception as exc: return ir.model_copy(update={"diagnostics": ir.diagnostics + (Diagnostic(code="extraction-failed", severity=Severity.ERROR, message=f"LLM extraction failed after retries: {exc}"),)})
4. Cache the result: ctx.llm_cache.set(checksum=ir.checksum.value, prompt_version=ctx.prompt_version, schema_version=ctx.schema_version, model_id=ctx.llm.model_id, value=result)
5. Return _apply_extraction(ir, result)

Define the private _apply_extraction(ir: Document, result) -> Document helper function:
- Extracts concept names from result.concepts (list of ExtractedConceptDTO) → tuple of name strings
- Extracts glossary terms from result.glossary (list of ExtractedGlossaryTermDTO) → tuple of term strings
- Extracts entity names from result.entities (list of ExtractedEntityDTO) → tuple of name strings
- Extracts reference targets from result.references (list of ExtractedReferenceDTO) → tuple of target strings
- Returns ir.model_copy(update={"concepts": <concepts tuple>, "glossary": <glossary tuple>, "entities": <entities tuple>, "references": <references tuple>})

Note: Document.concepts/glossary/entities/references are still typed as tuple[str, ...] from Phase 1 placeholder. The pass extracts the string fields from the DTOs and stores them as tuples of strings. Do not change the Document model field types in this plan.

Register the pass: @register_pass("extract_concepts", depends_on=("parse", "section", "metadata"))

Imports: from __future__ import annotations; from kir.core.domain.models.document import Document; from kir.core.domain.models.diagnostic import Diagnostic, Severity; from kir.core.passes.context import CompilerContext. Do NOT import from kir.llm in this file — the LLMPort seam via ctx.llm is the only access.

Update src/kir/compiler/documents/passes/__init__.py:
- Add extract_concepts to the forced import at the bottom: from . import parse, section, metadata, extract_concepts
- Keep everything else unchanged.

Create src/kir/compiler/documents/compiler.py:
- class DocumentCompiler with __init__(self, registry: PassRegistry, context: CompilerContext) -> None:
  - self._pipeline = registry.pipeline() — validates the dependency graph at construction time
  - self._ctx = context
- async def compile(self, source_path: Path) -> Document:
  - Read source text: text = source_path.read_text(encoding="utf-8")
  - Construct the initial Document IR: ir = Document(id="", title="", source=text, checksum=Checksum(value=""), language="")
  - Run each pass in pipeline order. Check if the pass function is a coroutine function: if asyncio.iscoroutinefunction(pass_fn): ir = await pass_fn(ir, self._ctx) else: ir = pass_fn(ir, self._ctx)
  - Return the final ir

Imports for compiler.py: from __future__ import annotations; import asyncio; from pathlib import Path; from kir.core.passes.context import CompilerContext; from kir.core.passes.registry import PassRegistry; from kir.core.domain.models.document import Document; from kir.core.domain.value_objects import Checksum.
  </action>
  <verify>
    <automated>grep -c "async def extract_concepts_pass" src/kir/compiler/documents/passes/extract_concepts.py && grep -c "extraction-failed" src/kir/compiler/documents/passes/extract_concepts.py && grep -c "ctx.llm_cache.get" src/kir/compiler/documents/passes/extract_concepts.py && grep -v '^#' src/kir/compiler/documents/passes/extract_concepts.py | grep -c "ctx.llm.extract" && python -c "from kir.compiler.documents.compiler import DocumentCompiler; print('ok')" && python -c "from kir.compiler.documents.passes import document_registry; p = document_registry.pipeline(); print(len(p) == 4)" && uv run pytest tests/core/ -x -q</automated>
  </verify>
  <done>ExtractConceptsPass registered and async; D-03 failure path produces Diagnostic without halting; cache hit/miss paths correct; DocumentCompiler.compile() runs all four passes in order; document_registry.pipeline() returns 4 passes; all core tests remain green.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| document sections → ctx.llm.extract() | Sections are user-supplied document content — passed as data to the LLM call, never into the fixed system prompt/instructions position |
| DocumentCompiler input path → filesystem | source_path.read_text() reads arbitrary filesystem paths; path traversal is acceptable here since DocumentCompiler is a batch CLI tool, not a web service — the operator controls the input corpus |
| LLM cache → Document IR | A cached result is applied to a different document only if the four-part key matches — LLMCacheKey.build() raises ValueError on empty components (already tested in Plan 02) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-09 | Tampering | Prompt injection via document sections | mitigate | Sections are passed as data to the user-turn position of Agent.run(prompt) — the prompt string built by PromptRegistry.render() is the user-side content that includes the sections; the Agent's system-level instructions (fixed contract) are separate. The extraction prompt template (extract_v1.md) must not include {sections} in a position that would be interpreted as system instructions. Enforced at prompt template authoring time. |
| T-02-10 | Tampering | Cross-document cache collision | mitigate | LLMCache.get() uses checksum (document-specific) as the first key component — two different documents have different checksums and cannot collide. Proven by test_no_cross_contamination (Plan 04b). |
| T-02-11 | Denial of Service | D-03 failure loop — extraction repeatedly fails | accept | output_retries=2 caps PydanticAI's retry loop at 3 total attempts; after exhaustion the exception propagates to the pass's except clause, which writes a Diagnostic and returns immediately. No infinite retry loop possible. |
| T-02-12 | Information Disclosure | API credentials in test output or logs | mitigate | All tests use FakeLLMAdapter — no real credentials are loaded or logged. ALLOW_MODEL_REQUESTS=False autouse fixture ensures even a misconfigured test path cannot reach a live API. |
| T-02-SC | Tampering | npm/pip/cargo installs | mitigate | slopcheck + blocking human checkpoint for any [ASSUMED]/[SUS] packages |
</threat_model>

<verification>
After task completes:
- python -c "from kir.compiler.documents.compiler import DocumentCompiler; print('ok')" prints "ok"
- python -c "from kir.compiler.documents.passes import document_registry; p = document_registry.pipeline(); print([f.__name__ for f in p])" prints all four pass names in dependency order
- grep -r "import pydantic_ai" src/kir/compiler/ returns zero matches
- grep -r "from kir.llm" src/kir/compiler/documents/passes/ returns zero matches (passes access LLM only via ctx.llm)
- uv run pytest tests/core/ -x -q passes (regression check on core tests)
</verification>

<success_criteria>
ExtractConceptsPass is async, registered with the correct depends_on tuple, implements cache hit/miss logic, and produces a Diagnostic on LLM failure without halting. DocumentCompiler wires all four passes and dispatches async passes with await. All core tests remain green.
</success_criteria>

<output>
Create .planning/phases/02-document-compiler/02-04a-SUMMARY.md when done.
</output>
