---
phase: 02-document-compiler
reviewed: 2026-07-01T00:00:00Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - src/kir/compiler/__init__.py
  - src/kir/compiler/documents/__init__.py
  - src/kir/compiler/documents/adapters/__init__.py
  - src/kir/compiler/documents/adapters/markdown_it_adapter.py
  - src/kir/compiler/documents/compiler.py
  - src/kir/compiler/documents/passes/__init__.py
  - src/kir/compiler/documents/passes/extract_concepts.py
  - src/kir/compiler/documents/passes/metadata.py
  - src/kir/compiler/documents/passes/parse.py
  - src/kir/compiler/documents/passes/section.py
  - src/kir/core/domain/models/document.py
  - src/kir/core/passes/context.py
  - src/kir/core/ports/llm_port.py
  - src/kir/core/ports/parser_port.py
  - src/kir/llm/__init__.py
  - src/kir/llm/cache.py
  - src/kir/llm/fake_adapter.py
  - src/kir/llm/prompts/__init__.py
  - src/kir/llm/prompts/extract_v1.md
  - src/kir/llm/prompts/registry.py
  - src/kir/llm/pydantic_ai_adapter.py
  - tests/compiler/__init__.py
  - tests/compiler/documents/__init__.py
  - tests/compiler/documents/conftest.py
  - tests/compiler/documents/fixtures/extract_concepts/expected_outputs.py
  - tests/compiler/documents/test_document_compiler.py
  - tests/compiler/documents/test_extract_concepts_pass.py
  - tests/compiler/documents/test_metadata_pass.py
  - tests/compiler/documents/test_parse_pass.py
  - tests/compiler/documents/test_section_pass.py
  - tests/conftest.py
  - tests/core/passes/fakes/fake_llm_port.py
  - tests/core/passes/fakes/fake_parser.py
  - tests/core/passes/test_context.py
  - tests/core/passes/test_pipeline_execution.py
  - tests/llm/test_cache.py
  - tests/llm/test_prompt_registry.py
  - tests/llm/test_pydantic_ai_adapter.py
findings:
  critical: 3
  warning: 5
  info: 5
  total: 13
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-01
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

Reviewed the full Phase 2 document-compiler implementation: four document passes (parse, section, metadata, extract_concepts), the DocumentCompiler orchestrator, the LLM adapter stack (PydanticAIAdapter, FakeLLMAdapter, LLMCache, PromptRegistry), and all associated tests.

The pipeline architecture is sound and the port boundaries are largely correct. All 116 tests pass. However, three blockers were found:

1. The `extract_v1.md` prompt template receives a Python object repr (`tuple[Section, ...].__str__()`) instead of readable Markdown text when rendered via `extract_concepts_pass`. The LLM sees `"(Section(heading='...', content='...'),)"` rather than structured section text. This silently produces a degraded extraction — the tests do not catch it because `FakeLLMAdapter` ignores `prompt` entirely.

2. `CompilerContext.llm_cache` is typed as `CachePort | None` but `extract_concepts_pass` calls `ctx.llm_cache.get(checksum=..., prompt_version=..., ...)` — keyword arguments that only `LLMCache` accepts, not `CachePort`. Injecting any legitimate `CachePort` implementation would produce a `TypeError` at runtime; the type declaration and the usage are incompatible.

3. `extract_concepts_pass` calls `ctx.prompts.render(...)` and `ctx.llm_cache.get(...)` unconditionally, but both fields default to `None` in `CompilerContext`. A context built without these fields (e.g., Phase 1 test context) will crash with `AttributeError`. `DocumentCompiler` does not validate the context before dispatching the pipeline.

---

## Critical Issues

### CR-01: Prompt renders Section objects as Python repr, not as document text

**File:** `src/kir/compiler/documents/passes/extract_concepts.py:84`

**Issue:** `ctx.prompts.render("extract_v1", sections=ir.sections)` passes `ir.sections` as a `tuple[Section, ...]`. `PromptRegistry.render()` calls `str.format(**kwargs)`, which invokes `__str__` on the tuple. The LLM receives a Python object repr as the document body:

```
## Document Sections

(Section(heading='Introduction', content='OAuth 2.0 is an authorization framework.'), Section(heading='Usage', content='...'))
```

The test in `test_prompt_registry.py` passes a raw string (`sections="# Test\n\nSome content."`) and does not exercise the real call path, so the bug is invisible to the test suite. In production, every extraction prompt sent to the LLM has unparseable, machine-formatted section content.

**Fix:** Serialize sections to readable text before passing to `render()`. A minimal fix is to format sections inline in the pass:

```python
# In extract_concepts.py, before render():
sections_text = "\n\n".join(
    f"### {s.heading}\n\n{s.content}" if s.heading else s.content
    for s in ir.sections
)
prompt: str = ctx.prompts.render("extract_v1", sections=sections_text)
```

Also update `test_prompt_registry.py` to pass a real `list[Section]` (or the formatted string derived from one) to catch this regression.

---

### CR-02: `CompilerContext.llm_cache` typed as `CachePort` but code requires `LLMCache`

**File:** `src/kir/core/passes/context.py:33` and `src/kir/compiler/documents/passes/extract_concepts.py:87-92`

**Issue:** `CompilerContext.llm_cache` is declared as `CachePort | None`, where `CachePort.get` takes a single positional `key: str`. But `extract_concepts_pass` calls it as:

```python
cached = ctx.llm_cache.get(
    checksum=ir.checksum.value,
    prompt_version=ctx.prompt_version,
    schema_version=ctx.schema_version,
    model_id=ctx.llm.model_id,
)
```

`LLMCache.get` accepts those keyword arguments, but no implementation of `CachePort` does. Injecting a type-correct `CachePort` (e.g., a raw `InMemoryCache`) would fail at runtime with `TypeError: get() got unexpected keyword arguments`. The `# type: ignore[union-attr]` comment suppresses the mismatch but does not fix it.

**Fix:** Change the field type to `LLMCache | None` (or define a `LLMCachePort` Protocol that matches `LLMCache`'s interface):

```python
# In context.py:
from kir.llm.cache import LLMCache  # if LLMCache moves to core/ or a port is defined

@dataclass(frozen=True, slots=True)
class CompilerContext:
    ...
    llm_cache: LLMCache | None = None
```

Alternatively, define a `LLMCachePort` protocol in `core/ports/` matching the 4-argument keyword interface and use that.

---

### CR-03: `extract_concepts_pass` crashes with `AttributeError` when `ctx.prompts` or `ctx.llm_cache` is `None`

**File:** `src/kir/compiler/documents/passes/extract_concepts.py:84,87,114`

**Issue:** Both `ctx.prompts` and `ctx.llm_cache` default to `None` in `CompilerContext`. `extract_concepts_pass` calls `ctx.prompts.render(...)` at line 84 and `ctx.llm_cache.get(...)` at line 87 with no null guard. If the pass is invoked through any code path using a Phase-1-style context (e.g., one of the `fake_compiler_context` fixtures in `tests/conftest.py`), the result is an unhandled `AttributeError` that is not a structured `Diagnostic` — it crashes the pipeline entirely.

The `# type: ignore[union-attr]` comments on lines 84, 87, and 114 acknowledge the nullable types without fixing them. The D-03 `except Exception` handler at line 99 only covers the LLM call (step 3), not steps 1 and 2 which fail before reaching it.

**Fix:** Add null checks at pass entry, failing loudly with a clear message before the D-03 handler has any chance to mask the misconfiguration:

```python
async def extract_concepts_pass(ir: Document, ctx: CompilerContext) -> Document:
    if ctx.prompts is None or ctx.llm_cache is None:
        raise ValueError(
            "extract_concepts_pass requires ctx.prompts and ctx.llm_cache to be set. "
            "Construct CompilerContext with prompt_version, llm_cache, and prompts."
        )
    ...
```

Alternatively, add a `DocumentCompiler.__init__` validation that checks these fields are non-None before accepting the context.

---

## Warnings

### WR-01: `MarkdownItAdapter` silently drops all code block content

**File:** `src/kir/compiler/documents/adapters/markdown_it_adapter.py:77-79`

**Issue:** The adapter captures only `inline` tokens (paragraph text), ignoring all other token types. The comment at line 79 says "their inline children carry the actual text." This is true for paragraphs, lists, and blockquotes — but `fence` tokens (code blocks) have their content in `token.content` directly, with no inline children. A document section containing only a code block will produce `Section(content='')` after extraction, silently discarding all code content. This affects concept extraction quality for code-heavy documentation.

```python
# Verified:
# Token type 'fence' has content='def foo():\n    pass\n'
# but is NOT of type 'inline', so it is ignored.
```

**Fix:** Handle `fence` tokens explicitly:

```python
elif token.type == "fence":
    if token.content:
        current_content_parts.append(token.content)
```

---

### WR-02: `MarkdownItAdapter` docstring contradicts implementation for blank input

**File:** `src/kir/compiler/documents/adapters/markdown_it_adapter.py:40-43`

**Issue:** The docstring states: "Returns `[Section(heading='', content='')]` for blank input." The actual implementation returns `[]` (empty list) for blank input due to the early-return guard at line 44 (`if not text or not text.strip(): return []`). Any caller relying on the docstring will be surprised and may introduce off-by-one bugs on empty documents.

**Fix:** Correct the docstring:

```python
Returns:
    A list of Section objects. Returns [] for blank or whitespace-only input.
    Returns a single preamble section if text has content but no headings.
```

---

### WR-03: `_slugify` produces identical IDs for distinct Unicode titles

**File:** `src/kir/compiler/documents/passes/metadata.py:21-32`

**Issue:** `_slugify` strips all non-ASCII characters with `re.sub(r"[^a-z0-9-]", "", slug)`. This means:
- "Café" → `"caf"` (accent stripped, different from "Cafeteria" → `"cafeteria"` but same as "CAF!" → `"caf"`)
- "C++" and "C#" both → `"c"` (collision; two different documents get the same id)
- "数学" (mathematics in Chinese) → `"untitled"` (total loss)

When two documents have the same slug, the compiler produces duplicate `Document.id` values with no detection or Diagnostic.

**Fix:** Either apply Unicode normalization before stripping (NFKD then encode to ASCII with `errors='ignore'`), or append the first 8 characters of the document checksum when a bare slug collision is possible:

```python
import unicodedata

def _slugify(title: str) -> str:
    # Normalize accents before stripping
    slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = slug.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"
```

---

### WR-04: `CompilerContext.prompts` typed as bare `object` with no port contract

**File:** `src/kir/core/passes/context.py:34`

**Issue:** `prompts: object = None` provides no type-checker-visible interface. `extract_concepts_pass` calls `ctx.prompts.render(...)` which requires `# type: ignore[union-attr]` to suppress the error. There is no `PromptRegistryPort` Protocol in `core/ports/` to define the contract, violating the hexagonal architecture principle (adapters behind domain-owned ports). A future alternative prompt source has nothing to implement against.

**Fix:** Define a `PromptRegistryPort` Protocol in `src/kir/core/ports/`:

```python
# src/kir/core/ports/prompt_port.py
from typing import Protocol

class PromptRegistryPort(Protocol):
    def render(self, name: str, **kwargs: object) -> str: ...
```

Then update `CompilerContext.prompts` to `PromptRegistryPort | None`.

---

### WR-05: `test_document_compiler_pipeline_has_four_passes` contains dead code

**File:** `tests/compiler/documents/test_document_compiler.py:168`

**Issue:** Line 168 calls `_, _ = _make_compiler_context()` and then immediately discards both results. The next lines construct a fresh context from scratch anyway. The first call is purely dead — it builds a `DocumentCompiler` that is never used, adding unnecessary overhead and confusing the reader.

```python
def test_document_compiler_pipeline_has_four_passes() -> None:
    _, _ = _make_compiler_context()  # <-- result unused; this line does nothing
    from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput
    adapter = FakeLLMAdapter(output=DocumentExtractionOutput())
    # ... builds a second compiler from scratch
```

**Fix:** Remove the dead call:

```python
def test_document_compiler_pipeline_has_four_passes() -> None:
    adapter = FakeLLMAdapter(output=DocumentExtractionOutput())
    ctx = CompilerContext(...)
    compiler = DocumentCompiler(document_registry, ctx)
    assert len(compiler._pipeline) == 4
```

---

## Info

### IN-01: Pervasive `from __future__ import annotations` violates project style guide

**File:** All 14 reviewed source files under `src/`

**Issue:** The project style guide (`.planning/STYLE_GUIDE.md`, confirmed in user memory) explicitly prohibits `from __future__ import annotations` across the KIR codebase. The rule states: "No real forward references exist in KIR; makes type evaluation implicit (violates explicit-is-better)." Every file in this phase was generated with this import, including: `compiler.py`, all four pass modules, both port modules (`llm_port.py`, `parser_port.py`), `context.py`, `cache.py`, `fake_adapter.py`, `pydantic_ai_adapter.py`, and `registry.py`.

**Fix:** Remove `from __future__ import annotations` from all 14 files. Replace any forward-reference strings (e.g., `"Section"`) with direct imports or restructure if a true cycle exists.

---

### IN-02: `if TYPE_CHECKING:` blocks used in port files

**File:** `src/kir/core/ports/llm_port.py:13-16`, `src/kir/core/ports/parser_port.py:5-8`

**Issue:** The project style guide prohibits `if TYPE_CHECKING:` because it masks coupling rather than fixing it. Both port files guard their `Section` import behind `TYPE_CHECKING`. Since `Section` is a domain model (not an adapter), this import should be direct.

**Fix:** Replace the guarded import with a direct one in both files:

```python
# Before:
from typing import TYPE_CHECKING, Protocol
if TYPE_CHECKING:
    from kir.core.domain.models.document import Section

# After:
from typing import Protocol
from kir.core.domain.models.document import Section
```

---

### IN-03: Dead assignment `fixture_path` in test

**File:** `tests/compiler/documents/test_extract_concepts_pass.py:140-142`

**Issue:** Lines 140-142 assign `fixture_path = (__file__)` — parentheses around `__file__` produce just `__file__`, and the variable `fixture_path` is never used afterward. This appears to be a leftover from a refactor.

```python
async def test_extract_concepts_pass_with_golden_fixture_doc_01() -> None:
    fixture_path = (
        __file__        # <-- assigned but never read
    )
    # Read the actual fixture file content
    import pathlib
    doc_path = pathlib.Path(__file__).parent / ...
```

**Fix:** Remove lines 140-142 entirely.

---

### IN-04: `_ErrorFakeLLMAdapter` (private-named class) directly imported from conftest

**File:** `tests/compiler/documents/test_extract_concepts_pass.py:25`

**Issue:** `_ErrorFakeLLMAdapter` is defined with a `_` prefix (conventionally private) in `tests/compiler/documents/conftest.py` but is explicitly imported by `test_extract_concepts_pass.py`. This breaks the encapsulation signal. Either the class should be public (rename to `ErrorFakeLLMAdapter`) or it should not be imported outside conftest (use `make_phase2_context(raise_error=...)` instead).

**Fix:** Use the already-provided `make_phase2_context(raise_error=error)` API, which wraps `_ErrorFakeLLMAdapter` internally:

```python
# Before:
from tests.compiler.documents.conftest import _ErrorFakeLLMAdapter, make_phase2_context
...
error_adapter = _ErrorFakeLLMAdapter(error)
ctx = _make_context_with_adapter(error_adapter)

# After:
from tests.compiler.documents.conftest import make_phase2_context
ctx = make_phase2_context(raise_error=error)
```

---

### IN-05: `block_real_llm_calls` fixture has incorrect return type annotation

**File:** `tests/conftest.py:26`

**Issue:** The fixture is a generator (it uses `yield`) but is annotated as `-> object`. The correct return type for a yield-based pytest fixture is `Generator[None, None, None]` (or simply omit the annotation). The incorrect annotation may confuse type checkers and hide the fact that cleanup (restoring `ALLOW_MODEL_REQUESTS`) runs post-yield.

**Fix:**

```python
from collections.abc import Generator

@pytest.fixture(autouse=True, scope="session")
def block_real_llm_calls() -> Generator[None, None, None]:
    original = pydantic_ai_models.ALLOW_MODEL_REQUESTS
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = False
    yield
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = original
```

---

_Reviewed: 2026-07-01_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
