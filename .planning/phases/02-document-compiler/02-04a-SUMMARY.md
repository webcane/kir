---
phase: 02-document-compiler
plan: "04a"
subsystem: document-compiler
tags: [async-pass, llm-cache, diagnostic, document-ir, pass-registry]

# Dependency graph
requires:
  - phase: 02-02
    provides: LLMCache, LLMCacheKey, InMemoryCache, FakeLLMAdapter, PromptRegistry
  - phase: 02-03
    provides: ParsePass, SectionPass, MetadataPass, document_registry, register_pass decorator
provides:
  - "ExtractConceptsPass: async LLM-backed extraction pass registered in document_registry"
  - "DocumentCompiler: service that wires all four passes into a runnable pipeline"
  - "D-03 failure handling: LLM exception writes Diagnostic without halting pipeline"
  - "LLM-02 cache integration: cache hit suppresses re-extraction"
affects:
  - 02-04b
  - 02-05

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Async pass pattern: async def pass_fn(ir, ctx) -> IR, dispatched with asyncio.iscoroutinefunction"
    - "D-03 failure path: bare except Exception, append Diagnostic, return without halting"
    - "LLMPort seam: pass accesses LLM only via ctx.llm and ctx.llm_cache — never imports kir.llm"
    - "DocumentCompiler: registry.pipeline() at construction validates dependency graph; compile() dispatches sync/async passes"

key-files:
  created:
    - src/kir/compiler/documents/passes/extract_concepts.py
    - src/kir/compiler/documents/compiler.py
  modified:
    - src/kir/compiler/documents/passes/__init__.py

key-decisions:
  - "Pass uses ctx.llm.model_id attribute on LLMPort — passes access LLM only via ctx, never import kir.llm directly"
  - "DocumentCompiler.compile() constructs initial Document with empty checksum (populated by MetadataPass) to avoid SHA-256 double-computation"
  - "_apply_extraction typed as object parameter to honor LLMPort seam — no direct import of DocumentExtractionOutput DTOs in pass code"

patterns-established:
  - "Async pass: async def, registered with depends_on, await ctx.llm.extract()"
  - "D-03 Diagnostic path: except Exception as exc → ir.model_copy(update={'diagnostics': ir.diagnostics + (Diagnostic(...),)})"
  - "DocumentCompiler: asyncio.iscoroutinefunction(pass_fn) gates await vs direct call"

requirements-completed: [DOC-01, DOC-02, DOC-03, LLM-01, LLM-02, LLM-03]

# Metrics
duration: 18min
completed: 2026-07-01
---

# Phase 02 Plan 04a: ExtractConceptsPass and DocumentCompiler Summary

**Async LLM-backed extraction pass with four-part cache key (LLM-02), D-03 diagnostic failure path, and DocumentCompiler service wiring all four passes into a runnable pipeline**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-01T07:00:00Z
- **Completed:** 2026-07-01T07:18:45Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments

- Implemented `extract_concepts_pass` as an async pass registered with `depends_on=("parse", "section", "metadata")` in `document_registry`
- Cache hit/miss logic: `ctx.llm_cache.get()` checked before LLM call; `ctx.llm_cache.set()` writes result on miss
- D-03 failure path: `except Exception as exc` appends a `Diagnostic(code="extraction-failed", severity=ERROR)` to the Document IR without halting the pipeline
- `_apply_extraction` helper converts `DocumentExtractionOutput` DTO lists into `tuple[str, ...]` for Document fields, honoring LLMPort seam (no kir.llm import)
- `DocumentCompiler` wires all four passes: `registry.pipeline()` at construction validates the dependency graph; `compile()` dispatches async passes with `await` and sync passes directly via `asyncio.iscoroutinefunction()`
- Updated `passes/__init__.py` forced import to include `extract_concepts`
- All 113 tests pass (64 core + 49 llm/compiler/tooling)

## Task Commits

1. **Task 1: ExtractConceptsPass (async, D-03 failure handling, cache integration) and DocumentCompiler service** - `5dfc942` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `src/kir/compiler/documents/passes/extract_concepts.py` — async extraction pass: prompt render, cache check, LLM call with D-03 guard, cache set, _apply_extraction
- `src/kir/compiler/documents/compiler.py` — DocumentCompiler class: pipeline validation at construction, async compile() method
- `src/kir/compiler/documents/passes/__init__.py` — added extract_concepts to forced import list

## Decisions Made

- `_apply_extraction` typed the `result` parameter as `object` to honor the LLMPort seam — the pass never imports `DocumentExtractionOutput` or any kir.llm type directly; attribute access via duck typing with `# type: ignore[attr-defined]` keeps mypy happy
- `DocumentCompiler.compile()` constructs the initial `Document` with an empty `Checksum(algorithm="sha256", value="")` — MetadataPass then populates the real SHA-256 checksum, avoiding double-computation at construction time
- `asyncio.iscoroutinefunction(pass_fn)` used at runtime to dispatch async vs sync passes — this handles a mixed pipeline without requiring every pass to become async

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `document_registry.pipeline()` now returns all four passes in dependency order
- `DocumentCompiler.compile(source_path)` is ready for integration testing in Plan 04b
- FakeLLMAdapter (from Plan 02-02) can be wired into CompilerContext to test extract_concepts_pass in isolation
- Plan 04b test fixtures can directly call `extract_concepts_pass(ir, ctx)` with a fake context

## Known Stubs

None — no placeholder values flow to rendering; Document fields are populated by real pass logic.

## Threat Flags

None — no new network endpoints, auth paths, or trust-boundary violations introduced. `source_path.read_text()` in `DocumentCompiler.compile()` follows the plan's accepted T-02 threat disposition (batch CLI tool, operator controls input corpus).

---

*Phase: 02-document-compiler*
*Completed: 2026-07-01*
