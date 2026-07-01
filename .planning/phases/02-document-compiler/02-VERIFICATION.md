---
phase: 02-document-compiler
verified: 2026-07-01T00:00:00Z
status: passed
score: 9/9
overrides_applied: 0
---

# Phase 02: Document-Compiler Verification Report

**Phase Goal:** Implement the DocumentCompiler service: four deterministic passes (parse, section, metadata, extract_concepts) wired through a registry-driven pipeline, with LLM-backed extraction, prompt templating, semantic caching, PydanticAI adapter, and a hexagonal boundary separating domain from LLM details.

**Verified:** 2026-07-01
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | All four passes exist and are registry-registered | VERIFIED | `@register_pass` in parse.py:15, section.py:14, metadata.py:34, extract_concepts.py:76; force-imported in passes/__init__.py:40 |
| 2 | DocumentCompiler wires them end-to-end | VERIFIED | compiler.py iterates `registry.pipeline()` with async dispatch; `test_document_compiler.py` — 3 integration tests all passing |
| 3 | ExtractConceptsPass uses ctx.llm/ctx.llm_cache/ctx.prompts (never imports pydantic_ai directly) | VERIFIED | No `kir.llm` import in extract_concepts.py; only imports from `kir.core.*` and `kir.compiler.documents.passes`; boundary rule documented in module docstring |
| 4 | LLMPort, LLMCachePort, PromptRegistryPort in `core/ports/` with no pydantic_ai imports | VERIFIED | All three protocols exist in `src/kir/core/ports/`; none import pydantic_ai; LLMPort imports only from `kir.core.domain.models.document`; LLMCachePort and PromptRegistryPort have no kir.llm imports |
| 5 | PydanticAIAdapter is the only file importing pydantic_ai | VERIFIED | `grep -rn "from pydantic_ai" src/` returns only `src/kir/llm/pydantic_ai_adapter.py` lines 14-15; `llm/__init__.py` contains only a docstring comment |
| 6 | Tests cover extraction pass, cache, prompt registry, and DocumentCompiler integration | VERIFIED | 52 Phase 2 tests collected; tests/llm/ covers cache+prompt+adapter; tests/compiler/documents/ covers all four passes + DocumentCompiler; 52 passed |
| 7 | `uv run pytest tests/ -q` passes with 121 tests | VERIFIED | `121 passed in 0.15s` — confirmed two independent runs |
| 8 | No `from __future__ import annotations` or `TYPE_CHECKING` in Phase 2 files | VERIFIED | Zero violations in all 14 Phase 2 source files (compiler.py, 4 passes, markdown_it_adapter.py, pydantic_ai_adapter.py, fake_adapter.py, cache.py, prompts/registry.py, context.py, llm_port.py, llm_cache_port.py, prompt_registry_port.py); existing violations are in Phase 1 files (registry.py, base.py, cache_port.py, repository_port.py) which are out of scope for this phase |
| 9 | Code review critical findings (CR-01/CR-02/CR-03) are resolved | VERIFIED | See detail below |

**Score:** 9/9 truths verified

---

## Code Review Critical Findings Resolution

### CR-01: Prompt renders Section objects as Python repr (RESOLVED)

**Finding:** `ctx.prompts.render("extract_v1", sections=ir.sections)` passed `tuple[Section, ...]` raw, producing Python object repr as LLM input.

**Resolution verified:** `extract_concepts.py` now contains `_sections_to_text()` (lines 28-41) which serializes each Section as `## {heading}\n\n{content}`. The pass calls `sections_text = _sections_to_text(ir.sections)` then `ctx.prompts.render("extract_v1", sections=sections_text)` (lines 107-108). The LLM receives readable Markdown text, not Python repr.

### CR-02: `CompilerContext.llm_cache` typed as `CachePort` not matching usage (RESOLVED)

**Finding:** Field was typed as `CachePort | None` but `extract_concepts_pass` called keyword-argument `get(checksum=..., prompt_version=..., schema_version=..., model_id=...)` which `CachePort.get` (single positional `key: str`) does not satisfy.

**Resolution verified:** `context.py` now imports and uses `LLMCachePort` (line 16: `from kir.core.ports.llm_cache_port import LLMCachePort`) and declares `llm_cache: LLMCachePort | None = None` (line 32). `LLMCachePort` in `core/ports/llm_cache_port.py` defines the exact four-keyword-argument `get/set` interface used by the pass — type and implementation are now aligned.

### CR-03: `extract_concepts_pass` crashes with AttributeError when `ctx.prompts`/`ctx.llm_cache` is None (RESOLVED)

**Finding:** Unconditional calls to `ctx.prompts.render(...)` and `ctx.llm_cache.get(...)` with no null guard; `# type: ignore[union-attr]` suppressed the type error without fixing it.

**Resolution verified:** Lines 103-104 in `extract_concepts.py` now contain an explicit null guard:
```python
if ctx.prompts is None or ctx.llm_cache is None:
    return ir
```
The pass returns the Document unmodified when Phase 2 dependencies are not wired in. The `# type: ignore` comments are gone. The WR-04 finding (prompts typed as bare `object`) is also resolved: `context.py` now declares `prompts: PromptRegistryPort | None = None`.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/kir/compiler/documents/passes/parse.py` | ParsePass | VERIFIED | `@register_pass("parse")` at line 15; substantive Markdown-it integration |
| `src/kir/compiler/documents/passes/section.py` | SectionPass | VERIFIED | `@register_pass("section", depends_on=("parse",))` at line 14 |
| `src/kir/compiler/documents/passes/metadata.py` | MetadataPass | VERIFIED | `@register_pass("metadata", depends_on=("parse", "section"))` at line 34 |
| `src/kir/compiler/documents/passes/extract_concepts.py` | ExtractConceptsPass | VERIFIED | `@register_pass("extract_concepts", depends_on=("parse", "section", "metadata"))` at line 76; async; 148 lines |
| `src/kir/compiler/documents/passes/__init__.py` | PassRegistry + force-imports | VERIFIED | `document_registry = PassRegistry()` + all 4 passes force-imported at line 40 |
| `src/kir/compiler/documents/compiler.py` | DocumentCompiler | VERIFIED | Iterates pipeline with async dispatch; 85 lines |
| `src/kir/compiler/documents/adapters/markdown_it_adapter.py` | MarkdownItAdapter | VERIFIED | exists, substantive; used by ParsePass via MarkdownParserPort |
| `src/kir/llm/pydantic_ai_adapter.py` | PydanticAIAdapter + DTOs | VERIFIED | 129 lines; DTOs, Agent setup, output validator, extract() method |
| `src/kir/llm/fake_adapter.py` | FakeLLMAdapter | VERIFIED | 44 lines; satisfies LLMPort structurally; tracks call_count |
| `src/kir/llm/cache.py` | LLMCache + InMemoryCache | VERIFIED | LLMCacheKey, LLMCache, InMemoryCache all present; 121 lines |
| `src/kir/llm/prompts/registry.py` | PromptRegistry | VERIFIED | Loads from prompts_dir, interpolates with str.format; PromptNotFoundError |
| `src/kir/llm/prompts/extract_v1.md` | Versioned extraction prompt | VERIFIED | 28 lines; structured prompt with four category instructions and rules |
| `src/kir/core/ports/llm_port.py` | LLMPort Protocol | VERIFIED | Protocol with `model_id: str` and `async extract(*, sections, prompt)`; no pydantic_ai import |
| `src/kir/core/ports/llm_cache_port.py` | LLMCachePort Protocol | VERIFIED | Protocol with 4-keyword `get/set`; created to resolve CR-02 |
| `src/kir/core/ports/prompt_registry_port.py` | PromptRegistryPort Protocol | VERIFIED | Protocol with `render(name, **kwargs) -> str`; created to resolve WR-04 |
| `src/kir/core/passes/context.py` | CompilerContext with Phase 2 fields | VERIFIED | `prompt_version`, `llm_cache: LLMCachePort | None`, `prompts: PromptRegistryPort | None` all present |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `extract_concepts.py` | `ctx.llm` (LLMPort) | `ctx.llm.extract(sections=..., prompt=...)` | WIRED | Line 122 |
| `extract_concepts.py` | `ctx.llm_cache` (LLMCachePort) | `.get(checksum=..., prompt_version=..., schema_version=..., model_id=...)` | WIRED | Lines 111-116 |
| `extract_concepts.py` | `ctx.prompts` (PromptRegistryPort) | `.render("extract_v1", sections=sections_text)` | WIRED | Line 108 |
| `DocumentCompiler` | `PassRegistry.pipeline()` | `registry.pipeline()` in `__init__` | WIRED | Line 45 |
| `DocumentCompiler.compile()` | each pass function | `asyncio.iscoroutinefunction` + `await` or direct call | WIRED | Lines 79-82 |
| `PydanticAIAdapter` | `pydantic_ai.Agent` | `Agent(model, output_type=DocumentExtractionOutput, ...)` | WIRED — isolated to llm/ | Line 95 |
| `LLMCache` | `CachePort` backend | `self._backend.get/set(key)` | WIRED | Lines 81, 91-92 |
| `PromptRegistry` | `extract_v1.md` | `path.read_text(encoding="utf-8")` + `template.format(**kwargs)` | WIRED | Lines 57-60 |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite passes 121 tests | `uv run pytest tests/ -q` | `121 passed in 0.15s` | PASS |
| Phase 2 tests (52) all pass | `uv run pytest tests/llm/ tests/compiler/documents/ -q` | `52 passed in 0.06s` | PASS |
| No pydantic_ai import outside llm/ | `grep -rn "from pydantic_ai" src/kir/compiler/ src/kir/core/` | no output | PASS |
| No style guide violations in Phase 2 files | grep for `from __future__`/`TYPE_CHECKING` in 14 Phase 2 files | no output | PASS |
| CR-01 fix: `_sections_to_text` serializes before render | grep for function + call in extract_concepts.py | found at lines 28, 107 | PASS |
| CR-02 fix: `LLMCachePort` typed in context | grep `llm_cache` in context.py | `LLMCachePort` at line 32 | PASS |
| CR-03 fix: null guard at pass entry | grep null guard in extract_concepts.py | found at line 103 | PASS |

---

## Anti-Patterns Found

No debt markers (TBD/FIXME/XXX) found in any Phase 2 source file.

The following style violations from the code review (IN-01/IN-02) were in Phase 1 files (`src/kir/core/passes/registry.py`, `src/kir/core/passes/base.py`, `src/kir/core/ports/cache_port.py`, `src/kir/core/ports/repository_port.py`) that are out of scope for Phase 2. They are carried forward as known pre-existing debt; the Phase 2 files themselves are clean.

| File | Pattern | Severity | Note |
|------|---------|----------|------|
| `core/passes/registry.py` | `from __future__ import annotations` | Warning | Phase 1 file; out of scope |
| `core/passes/base.py` | `from __future__ import annotations` + `TYPE_CHECKING` | Warning | Phase 1 file; out of scope |
| `core/ports/cache_port.py` | `from __future__ import annotations` | Warning | Phase 1 file; out of scope |
| `core/ports/repository_port.py` | `from __future__ import annotations` | Warning | Phase 1 file; out of scope |

---

## Human Verification Required

None. All critical behaviors are verifiable programmatically.

---

## Gaps Summary

No gaps. All nine verification criteria are met.

The three critical code review findings (CR-01: section serialization, CR-02: LLMCachePort type, CR-03: null guard) were all resolved in the implementation. The four warning findings (WR-01: code block content in MarkdownItAdapter, WR-02: docstring contradiction, WR-03: Unicode slugify collision, WR-05: dead test code) remain as open warnings but do not block the phase goal — they affect quality and edge-case correctness but not the primary goal of a working, correctly-bounded DocumentCompiler pipeline.

---

## Final Verdict

**PHASE GOAL ACHIEVED**

The DocumentCompiler service is implemented as specified: four deterministic, registry-registered passes (parse, section, metadata, extract_concepts) execute in dependency order through a pipeline. The LLM-backed extraction pass uses PydanticAI via the LLMPort hexagonal boundary — the domain never imports pydantic_ai. Semantic caching (LLMCache with LLMCachePort), prompt templating (PromptRegistry with extract_v1.md), and a PydanticAI adapter are all wired and tested. All 121 tests pass. No style guide violations in Phase 2 files.

---

_Verified: 2026-07-01T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
