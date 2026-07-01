---
plan: 02-02
phase: 02-document-compiler
status: complete
requirements:
  - LLM-01
  - LLM-02
  - LLM-03
key-files:
  created:
    - src/kir/llm/__init__.py
    - src/kir/llm/pydantic_ai_adapter.py
    - src/kir/llm/fake_adapter.py
    - src/kir/llm/cache.py
    - src/kir/llm/prompts/__init__.py
    - src/kir/llm/prompts/registry.py
    - src/kir/llm/prompts/extract_v1.md
    - tests/llm/test_cache.py
    - tests/llm/test_prompt_registry.py
    - tests/llm/test_pydantic_ai_adapter.py
---

## What Was Built

Complete `src/kir/llm/` package — the only zone in the codebase that imports `pydantic_ai`. Delivered in 3 tasks across 2 commits plus inline test completion.

### Task 1: LLM Package — DTOs, PydanticAIAdapter, FakeLLMAdapter

- **`src/kir/llm/pydantic_ai_adapter.py`**: Four frozen Pydantic DTOs (`ExtractedConceptDTO`, `ExtractedGlossaryTermDTO`, `ExtractedEntityDTO`, `ExtractedReferenceDTO`) and `DocumentExtractionOutput` (combined output_type). `PydanticAIAdapter` wraps `pydantic_ai.Agent` using v2 API names (`output_type=`, `result.output`, `retries={"output": N}`). Output validator rejects fully-empty extraction results via `ModelRetry`.
- **`src/kir/llm/fake_adapter.py`**: `FakeLLMAdapter` with configurable canned `DocumentExtractionOutput` and `call_count` tracking. Lives in `src/` (not `tests/`) for use as a production-tree test double.
- pydantic_ai import isolated to `pydantic_ai_adapter.py` only — zero imports in `core/` or `compiler/`.

### Task 2: LLM Cache Layer and Prompt Registry

- **`src/kir/llm/cache.py`**: `LLMCacheKey.build()` enforces all four components non-empty (raises `ValueError` otherwise) and returns colon-delimited key. `LLMCache` wraps any `CachePort` backend with keyword-only four-part API. `InMemoryCache` is the production `CachePort` implementation for Phase 2.
- **`src/kir/llm/prompts/registry.py`**: `PromptRegistry` loads versioned Markdown templates by name; raises `PromptNotFoundError` (subclass of `FileNotFoundError`) when template is missing; supports `**kwargs` interpolation via `str.format()`.
- **`src/kir/llm/prompts/extract_v1.md`**: Versioned extraction prompt defining all four categories (concept, glossary, entity, reference) with calibration example and `{sections}` placeholder.

### Task 3: Unit Tests

18 tests across 3 files, all green:
- `test_cache.py`: 9 tests covering four-component key validation, cache miss/hit/collision isolation
- `test_prompt_registry.py`: 4 tests covering template loading, `PromptNotFoundError`, interpolation, missing placeholder
- `test_pydantic_ai_adapter.py`: 5 tests covering `FakeLLMAdapter` structural conformance to `LLMPort`, `call_count`, `PydanticAIAdapter` plumbing with `TestModel`

## Deviations

**Sequential execution (no worktree isolation)**: Worktree agents for this plan were created from `origin/master` (`970ae2c`, Phase 1 tip) instead of local `master` (`a00e3dc`, post-wave-1 merge). Two worktree attempts failed the `worktree_branch_check` guard. Switched to sequential main-tree execution to complete the plan. Implementation result is identical.

**Test file from inline completion**: Task 3 tests were written inline by the orchestrator after the subagent hit a session usage limit mid-execution (after completing Tasks 1 and 2). Tests pass at `18/18`.

## Self-Check: PASSED

- `uv run pytest tests/llm/ -x -q` → 18 passed
- `uv run pytest tests/ -q` → 113 passed (full suite)
- `grep -r "import pydantic_ai" src/kir/core src/kir/compiler` → zero matches
- `grep "output_type=DocumentExtractionOutput" src/kir/llm/pydantic_ai_adapter.py` → match
- `grep "result.output" src/kir/llm/pydantic_ai_adapter.py` → match
- `src/kir/llm/prompts/extract_v1.md` exists and is non-empty
