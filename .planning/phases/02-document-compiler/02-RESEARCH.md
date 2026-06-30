# Phase 02: Document Compiler — Research

**Researched:** 2026-06-30
**Domain:** Deterministic Markdown parsing + LLM-backed structured extraction (PydanticAI) + response caching, in a hexagonal compiler-pass architecture
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01 (DOC-01):** Sections are detected heading-based, at any heading level (H1–H6) — every heading starts a new section. Content appearing before the first heading becomes an untitled preamble section.

**D-02 (DOC-03, LLM-01):** The LLM extraction pass makes one combined structured-output call per document — a single Pydantic output model returns concepts, glossary terms, entities, and references together, rather than four separate LLMPort calls.

**D-03 (DOC-03, cross-cutting with Phase 1 D-01):** If LLM extraction fails after PydanticAI's retries are exhausted, the document still produces a Document IR with empty concepts/glossary/entities/references, and a structured Diagnostic error is recorded. The document compile is never hard-failed by this pass.

**D-04 (LLM-03):** The golden/replay fixture corpus is small, hand-authored synthetic Markdown documents with hand-crafted expected extraction output — not real excerpts from project docs.

### Claude's Discretion

- Concrete Markdown parser library choice (e.g. `mistune` vs `markdown-it-py` vs others)
- Exact prompt versioning scheme (semver string, content hash, manual integer)
- Exact cache adapter implementation built atop Phase 1's generic `Cache` Protocol (in-memory vs file-based for this phase)

### Deferred Ideas (OUT OF SCOPE)

None. Cross-document concept merging, alias resolution, and knowledge-level taxonomy/conflict detection are confirmed Phase 3 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOC-01 | System parses a single Markdown source into Document IR (id, title, source, checksum, language, sections, concepts, glossary, entities, references) | Markdown parser adapter (markdown-it-py), Parse/Section/Metadata passes, Document model population |
| DOC-02 | Document IR for one document never merges information from another document | Stateless per-document pass chain; no shared mutable state; each Document IR built from a single source file's sections only |
| DOC-03 | System extracts concept mentions, glossary terms, entities, and references via an LLM-backed pass returning validated structured output | PydanticAI Agent with DocumentExtractionOutput as output_type; LLMPort isolation; combined one-call-per-doc extraction (D-02) |
| LLM-01 | LLM-backed passes depend only on LLMPort (domain-owned port), never directly on a specific LLM SDK | LLMPort Protocol narrowed to `extract(sections, prompt) -> ExtractionResult`; PydanticAIAdapter in `src/kir/llm/` only |
| LLM-02 | LLM responses cached keyed on (document checksum, prompt version, schema version, pinned model id) so reruns reproduce identical output without re-calling | `src/kir/llm/cache.py` builds LLM-specific cache key atop Phase 1's generic `CachePort` Protocol |
| LLM-03 | LLM-backed passes unit-tested against recorded responses (golden fixtures), zero live API calls in CI | `FakeLLMAdapter` for plumbing tests; `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` in conftest.py; hand-crafted `DocumentExtractionOutput` fixtures |
</phase_requirements>

---

## Summary

Phase 2 builds on a complete Phase 1 foundation (domain models, ports, PassRegistry, CompilerContext, YAML repository adapter all exist and are tested). The work falls into three parallel tracks:

**Track A — Deterministic Passes (DOC-01, DOC-02):** Three new passes (ParsePass, SectionPass, MetadataPass) register into the existing PassRegistry and transform a raw Markdown file into a populated Document IR. These require a Markdown parser adapter implementing `MarkdownParserPort` — `markdown-it-py` 4.2.0 is the recommended library (CommonMark-compliant, MIT, member of Google's Assured Open Source Software program, actively maintained). The passes are pure functions over domain models; no LLM involvement.

**Track B — LLM Infrastructure (LLM-01, LLM-02):** A new `src/kir/llm/` package is the only file in the codebase that imports `pydantic_ai`. It contains: `PydanticAIAdapter` implementing `LLMPort` via `Agent(output_type=DocumentExtractionOutput)`, a `FakeLLMAdapter` with canned responses for testing, a Prompt Registry loading versioned prompt templates from `llm/prompts/`, and `llm/cache.py` building the four-part cache key atop `CachePort`. The LLMPort Protocol in Phase 1 (`extract(self, text: str) -> object`) must be narrowed to match D-02's combined-extraction shape: `extract(self, *, sections: list[Section], prompt: str) -> ExtractionResult`.

**Track C — Extraction Pass + Tests (DOC-03, LLM-03):** `ExtractConceptsPass` is async, depends on Parse/Section/Metadata, calls `ctx.llm.extract(...)`, handles the cache hit/miss path, and catches exhausted retries as a `Diagnostic` per D-03. Tests use `FakeLLMAdapter` with canned `DocumentExtractionOutput` values — no VCR cassettes needed given D-04's hand-crafted approach.

**Primary recommendation:** Build in the order: (1) narrow LLMPort + add `FakeLLMAdapter`, (2) `markdown-it-py` adapter + ParsePass/SectionPass/MetadataPass, (3) `llm/cache.py` + Prompt Registry, (4) `PydanticAIAdapter`, (5) `ExtractConceptsPass`, (6) `DocumentCompiler` service wiring all five passes.

---

## Project Constraints (from CLAUDE.md)

The following directives apply to all planning and implementation in this phase:

- **No LLM SDK imports in `domain/` or `compiler/documents/passes/`** — `pydantic_ai` imports are permitted only in `src/kir/llm/`. Anti-Pattern 4 (ARCHITECTURE.md): never type `CompilerContext.llm` as `pydantic_ai.Agent`.
- **Passes communicate only through registry/pipeline, not direct imports** — `ExtractConceptsPass` must not import `ParsePass` or call it directly.
- **No rendering, query, or vector-search features** — extraction ends at persisting `DocumentExtractionOutput` fields into the `Document` IR; no downstream consumers are built.
- **Decision hierarchy:** Correctness → Determinism → Canonical Knowledge IR → Extensibility → Performance → Developer Convenience.
- **Definition of Done:** deterministic, independently tested, reproducible, versioned, documented, compatible with incremental compilation.
- **Immutable IR:** all passes use `ir.model_copy(update={...})`, never in-place mutation.
- **No global state:** `CompilerContext` threaded explicitly; no module-level singletons holding LLM client state.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Markdown parsing (raw bytes → parse tree) | `compiler/documents/adapters/` (MarkdownParserAdapter) | — | Adapter-ring concern; domain must never import `markdown_it` |
| Section splitting (parse tree → Section list) | `compiler/documents/passes/` (SectionPass) | — | Pure deterministic transformation; pass-ring owns it |
| Metadata extraction (checksum, title, language) | `compiler/documents/passes/` (MetadataPass) | — | Deterministic; reads Document fields only |
| LLM extraction (sections → concepts/glossary/entities/references) | `llm/` package (PydanticAIAdapter via LLMPort) | `compiler/documents/passes/` (ExtractConceptsPass orchestrates) | Adapter ring owns SDK; pass ring owns pass logic; port (domain ring) owns the seam |
| LLM response caching | `llm/cache.py` (CacheKey construction) + `core/ports/cache_port.py` (Protocol) | — | Cache-key construction is LLM-specific and lives in llm/ package; the generic CachePort lives in core/ (Phase 1) |
| Prompt versioning / prompt registry | `llm/prompts/` + `llm/prompts/registry.py` | — | LLM infrastructure concern; isolated in llm/ package |
| Document IR assembly and persistence | `compiler/documents/compiler.py` (DocumentCompiler service) | `tooling/repository/` (YAML persistence) | Use-case service orchestrates passes; repository adapter persists |
| Test doubles (fake LLM, fake cache) | `src/kir/llm/fake_adapter.py` (production-code fake) + `tests/` (test-only) | — | Fake adapter must be importable from production paths for DI; test-only fixtures stay in tests/ |

---

## Standard Stack

### Core (already in pyproject.toml — confirmed installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | >=2.13, 2.13.4 installed [VERIFIED: PyPI] | Domain models, Document IR, ExtractionOutput schema | Project foundation; all IR types are Pydantic BaseModels |
| ruamel-yaml | >=0.19, installed [VERIFIED: PyPI] | YAML serialization for Document IR persistence | Round-trip fidelity; already in pyproject.toml |
| pytest | >=8, 9.1.1 installed [VERIFIED: pypi.org] | Test runner | Project standard from Phase 1 |

### To Add for Phase 2

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic-ai-slim[openai,anthropic] | >=2.0,<3 (2.1.0 current) [VERIFIED: PyPI pypi.org/project/pydantic-ai] | PydanticAI adapter for LLM-backed extraction — provider-agnostic structured output | User-confirmed, STACK.md-documented choice; only file that imports it is `llm/pydantic_ai_adapter.py` |
| markdown-it-py | >=4.2.0 (4.2.0 current, released 2026-05-07) [VERIFIED: PyPI pypi.org/project/markdown-it-py] | Markdown parsing for ParsePass / MarkdownParserAdapter | CommonMark-compliant, MIT licensed, Python >=3.10 (project uses 3.13+), Google Assured OSS, actively maintained, referenced in ARCHITECTURE.md as candidate |
| pydantic-settings | >=2.x [ASSUMED] | `Settings(BaseSettings)` model for LLM provider/model configuration threaded through CompilerContext | STACK.md-recommended for typed config; validates `llm_model: str` (e.g. `"anthropic:claude-sonnet-4-6"`) |
| pytest-asyncio | >=0.21 (1.3.0 current) [VERIFIED: pypi.org/project/pytest-asyncio] | Async test runner — required because `ExtractConceptsPass` and `PydanticAIAdapter.extract()` are async | PydanticAI's async-first design requires async tests; STACK.md-specified |

### Supporting (development / testing)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-recording (VCR.py) | 0.13.4 [VERIFIED: PyPI pypi.org/project/pytest-recording] | Records/replays HTTP cassettes | Optional for this phase — D-04 specifies hand-crafted `FakeLLMAdapter` fixtures; VCR cassettes are useful if real recorded provider calls are ever needed in CI, but not required for the hand-crafted fixture approach |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| markdown-it-py | mistune | mistune is faster but less CommonMark-complete; ARCHITECTURE.md lists both as candidates — markdown-it-py wins on spec compliance, which matters for deterministic heading detection across edge cases (e.g. ATX-style headings with no space after `#`, setext headings) |
| markdown-it-py | python-markdown | Third alternative, extensive extension ecosystem but complex API; no advantage for this project's use case |
| FakeLLMAdapter + hand-crafted fixtures | pytest-recording VCR cassettes | VCR cassettes replay real provider HTTP responses — higher fidelity but require one live API call per fixture to record; D-04 decided hand-crafted expected output is simpler and sufficient for unit-level pass testing at this phase's scope |

**Installation:**
```bash
uv add "pydantic-ai-slim[openai,anthropic]>=2.0,<3" "markdown-it-py>=4.2.0" "pydantic-settings>=2"
uv add --dev "pytest-asyncio>=0.21" "pytest-recording"
```

---

## Package Legitimacy Audit

> slopcheck was not available in this environment. All packages below are tagged `[ASSUMED]` for slopcheck column. However, each package was verified against its authoritative PyPI listing and official documentation — slopcheck registry-existence is the only unverified step.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| pydantic-ai-slim | PyPI | ~1.5 yr (v0 since Dec 2024) | High (core pydantic ecosystem, millions of pydantic-ai installs) [ASSUMED] | github.com/pydantic/pydantic-ai | [ASSUMED] | Approved — official Pydantic team product, listed in official docs as preferred slim install |
| markdown-it-py | PyPI | ~5 yr | High — Google Assured OSS, conda-forge member [VERIFIED: pypi.org] | github.com/executablebooks/markdown-it-py | [ASSUMED] | Approved — well-established, Google-endorsed, actively maintained through 2026 |
| pydantic-settings | PyPI | ~4 yr | High (Pydantic team package) [ASSUMED] | github.com/pydantic/pydantic-settings | [ASSUMED] | Approved — official Pydantic team package |
| pytest-asyncio | PyPI | ~8 yr | Very high (pytest-dev org) [ASSUMED] | github.com/pytest-dev/pytest-asyncio | [ASSUMED] | Approved — official pytest-dev organization |
| pytest-recording | PyPI | ~5 yr (2025-05-08 latest) [VERIFIED: pypi.org] | Moderate | github.com/kiwicom/pytest-recording | [ASSUMED] | Approved — established VCR.py wrapper, no postinstall scripts |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none detected by source/age review

*slopcheck was unavailable. Planner should treat each install task as requiring a quick legitimacy spot-check (package age + source repo exists) before marking done — not a hard `checkpoint:human-verify` block, as all packages above have authoritative source confirmation from official docs or PyPI.*

---

## Architecture Patterns

### System Architecture Diagram

```
Markdown file (raw bytes)
        │
        ▼
MarkdownParserAdapter.parse()   [compiler/documents/adapters/markdown_it_adapter.py]
        │  (implements MarkdownParserPort — the only file importing markdown_it)
        ▼
ParsePass(ir, ctx)              [compiler/documents/passes/parse.py]
        │  (ir.sections = [raw token tree → Section list], heading-based per D-01)
        ▼
SectionPass(ir, ctx)            [compiler/documents/passes/section.py]
        │  (normalizes section content; preamble section for pre-H1 content)
        ▼
MetadataPass(ir, ctx)           [compiler/documents/passes/metadata.py]
        │  (populates id, title, checksum, language, source)
        ▼
ExtractConceptsPass(ir, ctx)    [compiler/documents/passes/extract_concepts.py]
        │  (async; checks LLM cache; calls ctx.llm.extract() via LLMPort seam)
        │
        ├──[cache HIT]──► ir.model_copy(update=_to_document_fields(cached))
        │
        └──[cache MISS]──►
                │
        PydanticAIAdapter.extract()  [llm/pydantic_ai_adapter.py]
                │  (the ONLY class that constructs pydantic_ai.Agent)
                │  Agent(model, output_type=DocumentExtractionOutput)
                │  await agent.run(prompt)  →  result.output
                │
        DocumentExtractionOutput     [llm/pydantic_ai_adapter.py — DTO]
        (concepts, glossary, entities, references — validated Pydantic model)
                │
                ├──[success]──► cache.set(key, result) → ir.model_copy(...)
                │
                └──[ModelRetry exhausted]──► Diagnostic(code="extraction-failed", severity=ERROR)
                                             ir.model_copy(update={"diagnostics": ...})
                                             (document IR still produced — D-03)
        │
        ▼
DocumentCompiler.compile(source_path)  [compiler/documents/compiler.py]
        │  (wires PassRegistry pipeline, threads CompilerContext, runs passes)
        ▼
Document IR (frozen Pydantic model, fully populated)
        │
        ▼
RepositoryPort.save(document_ir)  [tooling/repository/yaml_repository.py — Phase 1]
        │
        ▼
documents/<id>.yaml   (one file per document, deterministic output)
```

### Recommended Project Structure

Phase 1 delivered `src/kir/core/` and `src/kir/tooling/repository/`. Phase 2 adds:

```
src/kir/
├── core/                          # UNCHANGED from Phase 1 (except LLMPort narrowing)
│   └── ports/
│       └── llm_port.py            # Narrow to: extract(*, sections, prompt) -> ExtractionResult
│                                   # ExtractionResult = type alias for DocumentExtractionOutput
│
├── compiler/                      # NEW — Package 2 (imports core only)
│   └── documents/
│       ├── __init__.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   └── markdown_it_adapter.py  # Implements MarkdownParserPort via markdown_it
│       ├── passes/
│       │   ├── __init__.py             # MUST import all 4 pass modules (forces registration)
│       │   ├── parse.py                # ParsePass — heading-based section splitting (D-01)
│       │   ├── section.py              # SectionPass — section normalization
│       │   ├── metadata.py             # MetadataPass — id, title, checksum, language, source
│       │   └── extract_concepts.py     # ExtractConceptsPass — async, LLM-backed (DOC-03)
│       └── compiler.py                 # DocumentCompiler — wires 4 passes via PassRegistry
│
└── llm/                           # NEW — Package 3 (imports core only, the only pydantic_ai zone)
    ├── __init__.py
    ├── pydantic_ai_adapter.py     # PydanticAIAdapter(LLMPort) — Agent construction lives here
    ├── fake_adapter.py            # FakeLLMAdapter(LLMPort) — canned DocumentExtractionOutput
    ├── cache.py                   # LLM-02: build_key(checksum, prompt_version, schema_version, model_id)
    └── prompts/
        ├── __init__.py
        ├── registry.py            # PromptRegistry: load_prompt(name, version) -> str
        └── extract_v1.md          # First versioned prompt template

tests/
├── conftest.py                    # ADD: models.ALLOW_MODEL_REQUESTS = False + async mode config
├── compiler/
│   └── documents/
│       ├── __init__.py
│       ├── test_parse_pass.py
│       ├── test_section_pass.py
│       ├── test_metadata_pass.py
│       ├── test_extract_concepts_pass.py  # Uses FakeLLMAdapter + hand-crafted fixtures
│       ├── test_document_compiler.py      # End-to-end: .md → Document IR
│       └── fixtures/
│           └── extract_concepts/          # D-04: 10 synthetic .md + expected output pairs
│               ├── doc_01_rich.md
│               ├── doc_01_rich_expected.py  # (or .json) — hand-crafted DocumentExtractionOutput
│               └── ...
└── llm/
    ├── __init__.py
    ├── test_pydantic_ai_adapter.py    # Tests PydanticAIAdapter using FunctionModel/TestModel
    ├── test_cache.py                  # Tests cache key construction
    └── test_prompt_registry.py        # Tests prompt loading by name+version
```

### Pattern 1: LLMPort Narrowing for Combined Extraction (D-02)

**What:** Phase 1's `LLMPort` is a placeholder (`extract(self, text: str) -> object`). Phase 2 narrows it to match D-02's one-call-per-document combined extraction shape.

**When to use:** Before writing any pass or adapter — the port shape is the contract.

```python
# Source: CONTEXT.md D-02, AI-SPEC.md Section 3 [VERIFIED: project docs]
# src/kir/core/ports/llm_port.py
from __future__ import annotations
from typing import Protocol
from kir.core.domain.models.document import Section

class ExtractionResult(Protocol):
    """Structural type — satisfied by DocumentExtractionOutput from llm/ package.
    Defined here so domain/pass code never imports from llm/ directly."""
    concepts: list
    glossary: list
    entities: list
    references: list

class LLMPort(Protocol):
    model_id: str  # Exposed so cache key builder can read the pinned model id

    async def extract(
        self,
        *,
        sections: list[Section],
        prompt: str,
    ) -> ExtractionResult: ...
```

**Important:** `ExtractionResult` as a Protocol means the domain never needs to import `DocumentExtractionOutput` from the `llm/` package. Pass code only touches `LLMPort`.

### Pattern 2: PydanticAI Agent Construction (LLM-01)

**What:** `PydanticAIAdapter` is the only class that constructs `pydantic_ai.Agent`. Uses `output_type=DocumentExtractionOutput`, `retries={"output": 2}`, low temperature for determinism.

```python
# Source: AI-SPEC.md Section 3, pydantic.dev/docs/ai/core-concepts/output/ [VERIFIED: official docs]
# src/kir/llm/pydantic_ai_adapter.py
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.models.settings import ModelSettings

class PydanticAIAdapter:
    model_id: str  # satisfies LLMPort.model_id

    def __init__(self, model: str, *, max_output_retries: int = 2):
        self.model_id = model
        self._agent = Agent(
            model,
            output_type=DocumentExtractionOutput,
            retries={"output": max_output_retries},
            model_settings=ModelSettings(temperature=0.1, max_tokens=4096),
        )

        @self._agent.output_validator
        async def _non_empty(output: DocumentExtractionOutput) -> DocumentExtractionOutput:
            if not any([output.concepts, output.glossary, output.entities, output.references]):
                raise ModelRetry("All four extraction categories are empty — re-read and retry.")
            return output

    async def extract(self, *, sections: list[Section], prompt: str) -> DocumentExtractionOutput:
        result = await self._agent.run(prompt)
        return result.output  # v2 API: .output not .data
```

### Pattern 3: Cache Key Construction (LLM-02)

**What:** `llm/cache.py` builds a four-part cache key string, delegating storage to `CachePort` (Phase 1 generic Protocol). Key = `checksum_value:prompt_version:schema_version:model_id`.

```python
# Source: CONTEXT.md D-02 cache-key spec, ARCHITECTURE.md §LLM response cache [VERIFIED: project docs]
# src/kir/llm/cache.py
from __future__ import annotations
from kir.core.ports.cache_port import CachePort

class LLMCacheKey:
    def build(
        self,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
    ) -> str:
        if not all([checksum, prompt_version, schema_version, model_id]):
            raise ValueError("All four cache key components must be non-empty (LLM-02 integrity)")
        return f"{checksum}:{prompt_version}:{schema_version}:{model_id}"

class LLMCache:
    def __init__(self, backend: CachePort):
        self._backend = backend
        self._key_builder = LLMCacheKey()

    def get(self, checksum, prompt_version, schema_version, model_id):
        key = self._key_builder.build(checksum, prompt_version, schema_version, model_id)
        return self._backend.get(key)

    def set(self, checksum, prompt_version, schema_version, model_id, value):
        key = self._key_builder.build(checksum, prompt_version, schema_version, model_id)
        self._backend.set(key, value)
```

### Pattern 4: ExtractConceptsPass (DOC-03, D-03)

**What:** Async pass that checks the cache, calls `ctx.llm.extract()`, handles D-03 failure gracefully.

```python
# Source: AI-SPEC.md Section 4 [VERIFIED: project docs]
# src/kir/compiler/documents/passes/extract_concepts.py
from kir.core.passes.registry import register_pass  # note: document-compiler has its own registry instance
from kir.core.domain.models.document import Document
from kir.core.domain.models.diagnostic import Diagnostic, Severity
from kir.core.passes.context import CompilerContext

@register_pass("extract_concepts", depends_on=("parse", "section", "metadata"))
async def extract_concepts_pass(ir: Document, ctx: CompilerContext) -> Document:
    prompt = ctx.prompts.render("extract_v1", sections=ir.sections)
    cached = ctx.llm_cache.get(
        checksum=ir.checksum.value,
        prompt_version=ctx.prompt_version,
        schema_version=ctx.schema_version,
        model_id=ctx.llm.model_id,
    )
    if cached is not None:
        return _apply_extraction(ir, cached)

    try:
        result = await ctx.llm.extract(sections=ir.sections, prompt=prompt)
    except Exception as exc:  # output_retries exhausted — D-03
        return ir.model_copy(update={
            "diagnostics": ir.diagnostics + (
                Diagnostic(
                    code="extraction-failed",
                    severity=Severity.ERROR,
                    message=f"LLM extraction failed after retries: {exc}",
                ),
            )
        })

    ctx.llm_cache.set(
        checksum=ir.checksum.value,
        prompt_version=ctx.prompt_version,
        schema_version=ctx.schema_version,
        model_id=ctx.llm.model_id,
        value=result,
    )
    return _apply_extraction(ir, result)
```

### Pattern 5: Test Setup — ALLOW_MODEL_REQUESTS=False (LLM-03)

**What:** Global safety net so any misconfigured test that doesn't override its model with a fake will fail loudly instead of burning real API quota.

```python
# Source: pydantic.dev/docs/ai/guides/testing/ [VERIFIED: official docs]
# tests/conftest.py (add to existing conftest)
import pytest
from pydantic_ai import models as pydantic_ai_models

@pytest.fixture(autouse=True)
def block_real_llm_calls():
    """Ensure zero live API calls in CI — LLM-03."""
    original = pydantic_ai_models.ALLOW_MODEL_REQUESTS
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = False
    yield
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = original
```

**Note:** Per current PydanticAI docs, the testing guide recommends `pytestmark = pytest.mark.anyio` for async tests using anyio — verify whether `pytest-asyncio` or `anyio` is the right pairing against the installed version before scaffolding.

### Pattern 6: Prompt Versioning (Claude's Discretion)

**Recommendation:** Use a simple integer version embedded in the filename (`extract_v1.md`, `extract_v2.md`) with the version string `"1"`, `"2"` etc. as the `prompt_version` constant in `core/config/versions.py` (where `prompt_version = "1"` is already pre-declared from Phase 1). This is the simplest scheme consistent with the project's existing `prompt_version`-as-tracked-field convention. A content hash would require the prompt file to be read at config-load time (adds I/O to initialization); semver adds complexity without benefit at this scale. Changing any prompt content = bump `prompt_version` constant + rename/add prompt file.

### Pattern 7: Cache Backend for This Phase (Claude's Discretion)

**Recommendation:** Use an **in-memory dict** as the `CachePort` implementation for Phase 2. Phase 1's `FakeCache` (a dict-backed `CachePort`) already exists in `tests/`; a production-grade in-memory `InMemoryCache` in `src/kir/llm/` or `src/kir/tooling/` is the right starting point. File-based caching (SQLite, shelve, JSON) would satisfy LLM-02's reproducibility goal better across process restarts, but adds complexity not required by any Phase 2 success criterion — the success criteria only require that the cache works within a single compile run. Flag file-based caching as a Phase 5 (Incremental Compilation) concern.

### Anti-Patterns to Avoid

- **Importing `pydantic_ai` anywhere outside `src/kir/llm/`** — the single most important constraint from CLAUDE.md and ARCHITECTURE.md Anti-Pattern 4.
- **Making `ExtractConceptsPass` synchronous** — `Agent.run_sync()` inside an async pipeline raises `RuntimeError: asyncio.run() cannot be called from a running event loop`. Use `async def` + `await agent.run()` everywhere.
- **Using `TestModel` for golden-fixture regression tests** — `TestModel` generates schema-satisfying garbage, not realistic extraction data. Per AI-SPEC.md pitfall #4: use `FakeLLMAdapter` with hand-crafted `DocumentExtractionOutput` values for D-04 fixtures.
- **Forgetting to import pass modules in `__init__.py`** — decorator registration fires on import only. A pass not imported is a pass never registered. `compiler/documents/passes/__init__.py` must import all four pass modules.
- **Using v1 PydanticAI API names** — `result_type`, `.data`, `result_retries` are renamed in v2.0.0: `output_type`, `.output`, `output_retries`. Any snippet predating mid-2026 may use old names.
- **Missing `diagnostics` field on Document** — the existing `Document` model in Phase 1 has no `diagnostics: tuple[Diagnostic, ...]` field. This must be added before D-03's failure-handling pattern can work (the pass needs `ir.diagnostics + (diag,)`).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown parsing | Custom regex heading detector | `markdown-it-py` via `MarkdownParserAdapter` | CommonMark edge cases (setext headings, escaped `#`, inline code containing `#`) are numerous and well-tested in markdown-it-py; regex misses them |
| LLM structured output + retries | Manual JSON repair, `json.loads()` with retry loop | `pydantic_ai.Agent(output_type=Model)` | PydanticAI handles schema generation, JSON extraction from provider responses, and `ModelRetry`/retry counting — re-implementing this is precisely what AI-SPEC.md flags as "don't build" |
| Provider-agnostic model switching | Per-provider if/else branches | PydanticAI model-string switch (`"anthropic:..."`, `"openai:..."`) | PydanticAI's architecture — one `Agent`, different model strings — directly satisfies LLM-01 provider substitutability |
| LLM output validation | Custom schema validators | `output_type=DocumentExtractionOutput` (Pydantic validates automatically) + `@agent.output_validator` for semantic checks | Schema validation is free; `output_validator` for the non-empty check costs one model round-trip only when needed |
| Token estimation for prompt budget | Hand-rolled tokenizer | Not needed for Phase 2 | Documents at v1 scale are well within 128K context windows per AI-SPEC.md Section 4b; section-budget splitting is a forward-looking note only |

**Key insight:** Both the Markdown parsing and LLM structured-output domains have well-tested, widely-deployed libraries that handle years of edge cases. Hand-rolling either would produce a worse, less-deterministic result — which directly violates the project's core value.

---

## Common Pitfalls

### Pitfall 1: PydanticAI v1 API Names (v2 renamed critical surface)

**What goes wrong:** Code written from training data, blog posts, or any pre-2026-06-23 source uses `result_type=`, `.data`, or `result_retries=`. In v2.0.0, these names either raise `TypeError: unexpected keyword argument` (the loud failure) or silently no-op if passed via `**kwargs` (the dangerous failure).
**Why it happens:** PydanticAI v2.0.0 shipped six days before this research was run. The vast majority of online examples, documentation mirrors, and training data predate the rename.
**How to avoid:** Use ONLY the v2 names: `output_type=`, `result.output`, `retries={"output": N}`. Add a CI check: `grep -r "result_type\|\.data\b\|result_retries" src/kir/llm/` should return zero matches.
**Warning signs:** `TypeError: unexpected keyword argument 'result_type'` at Agent construction time; `AttributeError: 'RunResult' object has no attribute 'data'` at result access time.

### Pitfall 2: Synchronous Agent Call Inside Async Pipeline

**What goes wrong:** `Agent.run_sync()` called from inside an async pass or an `asyncio.run()` context raises `RuntimeError: asyncio.run() cannot be called from a running event loop`.
**Why it happens:** `Agent.run_sync()` internally calls `asyncio.run()`. If there is already an event loop running (pytest-asyncio, an async pass), this is illegal.
**How to avoid:** `ExtractConceptsPass` must be `async def`. `PydanticAIAdapter.extract()` must `await self._agent.run(...)`. Never use `run_sync()` in any production path.
**Warning signs:** `RuntimeError: This event loop is already running` or `RuntimeError: asyncio.run() cannot be called from a running event loop`.

### Pitfall 3: Pass Module Not Imported → Never Registered

**What goes wrong:** The `@register_pass` decorator fires at import time. If `compiler/documents/passes/extract_concepts.py` is never imported, the pass is never registered. The pipeline builds with only the imported passes, and the missing pass produces no error (the dependency declaration `depends_on=("parse", "section", "metadata")` is what would catch a missing pass at `pipeline()` build time, but only if the dependent pass IS imported).
**Why it happens:** Python's decorator-as-registration pattern is non-obvious: writing the pass file is not enough.
**How to avoid:** `compiler/documents/passes/__init__.py` must explicitly import all four pass modules (`from . import parse, section, metadata, extract_concepts`). Verify with an integration test that `len(registry.pipeline()) == 4`.
**Warning signs:** Document IR with unpopulated fields but no diagnostic, or `MissingDependencyError` during `pipeline()` build naming a pass that is never registered.

### Pitfall 4: Document Model Missing `diagnostics` Field

**What goes wrong:** The existing `Document` model (Phase 1) does not have a `diagnostics: tuple[Diagnostic, ...]` field. D-03 requires `ir.model_copy(update={"diagnostics": ir.diagnostics + (diag,)})`. Without the field, `ir.diagnostics` raises `AttributeError`, and `model_copy` with `extra="forbid"` would reject the key.
**Why it happens:** Phase 1 deliberately deferred diagnostics-on-Document to Phase 2 (the field isn't needed until a real pass can fail). The placeholder comment in `document.py` (`# Phase 2's extraction pass will replace this`) is a reminder, but the field addition is easy to forget.
**How to avoid:** The first plan wave must add `diagnostics: tuple[Diagnostic, ...] = ()` to `Document` in `core/domain/models/document.py`, and update existing Phase 1 tests to pass.
**Warning signs:** `AttributeError: 'Document' object has no attribute 'diagnostics'` or Pydantic `ValidationError` on `model_copy(update={"diagnostics": ...})`.

### Pitfall 5: Cache Key with Missing Component

**What goes wrong:** If any of the four cache key components (checksum, prompt_version, schema_version, model_id) is empty or `None`, the resulting key is degenerate. Two different documents could produce the same cache key (e.g., empty model_id), causing a cache collision where one document's extraction is silently returned for another's lookup.
**Why it happens:** `model_id` is easy to forget — it requires the `PydanticAIAdapter` (or `FakeLLMAdapter`) to expose the exact resolved model string, not just accept it opaquely in the constructor.
**How to avoid:** `LLMCacheKey.build()` must validate all four components are non-empty and raise `ValueError` loudly if any is missing (AI-SPEC.md Section 6 guardrail: "must fail loudly rather than silently caching under a degenerate/partial key").
**Warning signs:** Cache hit rate unexpectedly high across different documents; Document IR A containing extraction from document B's content.

### Pitfall 6: MarkdownParserPort Return Type Too Loose

**What goes wrong:** Phase 1's `MarkdownParserPort.parse()` returns `object`. If the adapter returns markdown-it-py's internal `Token` list directly (a library-specific type), then `ParsePass` would need to import `markdown_it` to process it — violating the hexagonal boundary.
**Why it happens:** The Phase 1 port is intentionally a placeholder. Phase 2 must define a concrete return type that is domain-safe (e.g., a simple `ParsedDocument` dataclass/DTO containing raw section strings and heading levels) so the pass never sees `markdown_it` types.
**How to avoid:** Define a `ParsedDocument` DTO (or expand Section) in `core/domain/models/document.py` that the adapter populates using markdown-it-py internals, and the pass receives. Alternatively, the adapter returns `list[Section]` directly (already a domain type), keeping ParsePass trivially thin.
**Warning signs:** `import markdown_it` appearing in any file outside `compiler/documents/adapters/`.

---

## Code Examples

### Heading-Based Section Splitting with markdown-it-py (D-01)

```python
# Source: markdown-it-py documentation, interpreted for this project's D-01 rule
# compiler/documents/adapters/markdown_it_adapter.py
from markdown_it import MarkdownIt
from kir.core.domain.models.document import Section

def parse_sections_from_markdown(text: str) -> list[Section]:
    """Split Markdown text into Sections at every heading level (H1-H6).
    Content before the first heading becomes a preamble section (heading='')."""
    md = MarkdownIt()
    tokens = md.parse(text)

    sections: list[Section] = []
    current_heading = ""
    current_content_parts: list[str] = []

    for token in tokens:
        if token.type == "heading_open":
            # Save previous section if content exists
            if current_content_parts or sections:  # always save if we've started
                sections.append(Section(heading=current_heading,
                                        content="\n".join(current_content_parts).strip()))
            current_heading = ""
            current_content_parts = []
        elif token.type == "inline" and tokens[tokens.index(token) - 1].type == "heading_open":
            current_heading = token.content
        elif token.type not in ("heading_open", "heading_close"):
            if hasattr(token, "content") and token.content:
                current_content_parts.append(token.content)

    # Final section
    if current_content_parts or current_heading:
        sections.append(Section(heading=current_heading,
                                content="\n".join(current_content_parts).strip()))

    return sections
```

**Note:** The exact token iteration logic must be verified against markdown-it-py's actual token stream structure. Inline content for headings is in a child `inline` token; use `token.children` or the `inline` block properly. The above is a schematic, not a production-ready implementation — the implementing agent must verify against markdown-it-py docs.

### FakeLLMAdapter for Golden Fixture Tests (LLM-03, D-04)

```python
# Source: AI-SPEC.md Section 3 Pitfall #4, project pattern
# src/kir/llm/fake_adapter.py
from __future__ import annotations
from kir.core.domain.models.document import Section
from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput

class FakeLLMAdapter:
    """Canned-response LLM adapter for pass plumbing tests and golden-fixture replay.
    Satisfies LLMPort structurally. Configured with a fixed output or per-call callable."""

    model_id: str = "fake:v0"

    def __init__(self, output: DocumentExtractionOutput | None = None):
        self._output = output or DocumentExtractionOutput()
        self._call_count = 0

    async def extract(self, *, sections: list[Section], prompt: str) -> DocumentExtractionOutput:
        self._call_count += 1
        return self._output

    @property
    def call_count(self) -> int:
        return self._call_count
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PydanticAI `result_type=` | `output_type=` | v2.0.0, 2026-06-23 | All pre-2026-06-23 examples use the wrong kwarg name |
| `result.data` | `result.output` | v2.0.0, 2026-06-23 | Silent `AttributeError` if old name used |
| `result_retries=N` | `retries={"output": N}` | v2.0.0, 2026-06-23 | Old kwarg ignored or raises `TypeError` |
| `pydantic-ai` full bundle | `pydantic-ai-slim[provider]` preferred | v2.0.0 (extras syntax stable earlier) | Slim install avoids unnecessary provider extras; project uses one provider at a time |
| `@agent.output_validator` takes only the output | `@agent.output_validator` can take `ctx: RunContext` + output (optional `ctx`) | v2 | Validator signature is flexible; use `async def _validate(output: T) -> T` form |

**Deprecated/outdated:**
- PydanticAI v1 testing guide (`Agent.override(model=TestModel())`): still valid pattern in v2, but `pytestmark = pytest.mark.anyio` is the recommended async test mode — verify with installed `pytest-asyncio` version whether `asyncio_mode = "auto"` in `pyproject.toml` or `anyio` marks are used.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pydantic-settings` is the right package for typed LLM model/provider config | Standard Stack | Low — it's the Pydantic team package; could use dataclass or plain dict if settings are simple |
| A2 | In-memory dict is sufficient cache backend for Phase 2 (no file persistence needed) | Pattern 7 | Low — if success criterion 4 (cache hit on rerun) is interpreted as "across process restarts," file-based cache would be needed; but re-reading the criterion it says "same compile run," so in-memory is sufficient |
| A3 | `pytestmark = pytest.mark.anyio` OR `asyncio_mode = "auto"` in `pyproject.toml` is the right pytest-asyncio async test configuration | Pattern 5, Validation Architecture | Low-medium — PydanticAI docs recommend `anyio`; pytest-asyncio 1.x may have changed its default mode. The implementing agent must verify the exact config against the installed pytest-asyncio version before writing tests |
| A4 | `FakeLLMAdapter` lives in `src/kir/llm/fake_adapter.py` (production source tree, not tests/) | Project Structure | Medium — if it's test-only, `tests/` is the right location; but it should be importable by the `DocumentCompiler` for DI at composition time in non-CI environments |
| A5 | `Document` model needs `diagnostics: tuple[Diagnostic, ...]` added in Phase 2 | Pitfall 4 | High if wrong — D-03's failure-handling pattern will not compile without this field |
| A6 | `MarkdownParserPort.parse()` return type should be changed to `list[Section]` (or a new DTO) rather than kept as `object` | Pitfall 6 | Medium — keeping `object` is safe for now if both adapter and pass are written consistently; but the hexagonal boundary violation is a real risk |

---

## Open Questions

1. **async test runner: anyio vs pytest-asyncio auto mode**
   - What we know: PydanticAI's testing guide recommends `pytestmark = pytest.mark.anyio`; project currently uses `pytest` with no async configuration
   - What's unclear: whether pytest-asyncio 1.3.0 requires `asyncio_mode = "auto"` in `pyproject.toml` or whether the `@pytest.mark.asyncio` decorator per-test is preferred
   - Recommendation: Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in pyproject.toml; verify it works with a single async test before committing to the pattern for all extraction pass tests

2. **Where FakeLLMAdapter should live**
   - What we know: Phase 1's fake adapters live in `tests/core/passes/fakes/`; the new `FakeLLMAdapter` is needed both in tests (golden fixtures) and potentially at the `DocumentCompiler` composition root for non-live usage
   - What's unclear: whether the planner should put it in `src/kir/llm/fake_adapter.py` (usable everywhere) or `tests/` (test-only, cleaner boundary)
   - Recommendation: `src/kir/llm/fake_adapter.py` — consistent with ARCHITECTURE.md's build-order step 5 ("Build fake/mock LLM adapter before real one"); it is a legitimate non-live implementation of LLMPort, not a test-only artifact

3. **CompilerContext extension for Phase 2 fields**
   - What we know: Phase 1's `CompilerContext` has `llm`, `repository`, `parser`, `compiler_version`, `schema_version`. Phase 2's `ExtractConceptsPass` also needs `prompt_version`, `llm_cache`, and a `prompts` (Prompt Registry) reference.
   - What's unclear: whether to extend `CompilerContext` with these fields (changes a Phase 1 artifact) or use a `DocumentCompilerContext` subclass
   - Recommendation: Extend `CompilerContext` directly — `prompt_version` is already pre-declared in `core/config/versions.py` as a placeholder, signaling this was the intended home; `llm_cache` and `prompts` are natural additions to the "explicit dependency-injection container" that `CompilerContext` is

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (uv venv) | All passes | ✓ | 3.13.13 [VERIFIED: uv run python --version] | — |
| uv | Package management | ✓ | 0.11.7 [VERIFIED: uv --version] | — |
| pytest | Test runner | ✓ | 9.1.1 (in project venv) [VERIFIED] | — |
| pydantic | Domain models | ✓ | 2.13.4 (installed) [VERIFIED] | — |
| ruamel-yaml | YAML persistence | ✓ | Installed (ruamel.yaml ok) [VERIFIED] | — |
| pydantic-ai-slim | LLM adapter | ✗ | Not yet installed | Must install: `uv add "pydantic-ai-slim[openai,anthropic]>=2.0,<3"` |
| markdown-it-py | Markdown parsing | ✗ | Not yet installed | Must install: `uv add "markdown-it-py>=4.2.0"` |
| pydantic-settings | Config management | ✗ | Not yet installed | Must install: `uv add "pydantic-settings>=2"` |
| pytest-asyncio | Async test runner | ✗ | Not yet installed | Must install: `uv add --dev "pytest-asyncio>=0.21"` |
| npx (for Promptfoo eval, optional) | Promptfoo regression suite | ✓ | 11.17.0 [VERIFIED] | — |
| LLM API credentials (Anthropic/OpenAI) | PydanticAIAdapter live calls | Unknown | — | FakeLLMAdapter bypasses — no live calls in CI |

**Missing dependencies with no fallback:** `pydantic-ai-slim`, `markdown-it-py` — both are required for Phase 2 core functionality and must be installed in Wave 0.

**Missing dependencies with fallback:** `pydantic-settings` — plain `os.environ` or a hardcoded `Settings` dataclass works as a fallback; `pytest-asyncio` — `anyio` marks may substitute.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (installed) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/compiler/documents/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DOC-01 | Single Markdown → Document IR with all fields | integration | `uv run pytest tests/compiler/documents/test_document_compiler.py -x` | ❌ Wave 0 |
| DOC-01 | Heading-based section splitting (all H1–H6, preamble) | unit | `uv run pytest tests/compiler/documents/test_parse_pass.py -x` | ❌ Wave 0 |
| DOC-01 | Metadata pass populates id, title, checksum, language, source | unit | `uv run pytest tests/compiler/documents/test_metadata_pass.py -x` | ❌ Wave 0 |
| DOC-02 | Two documents compiled independently share zero extracted content | integration | `uv run pytest tests/compiler/documents/test_document_compiler.py::test_no_cross_contamination -x` | ❌ Wave 0 |
| DOC-03 | ExtractConceptsPass calls ctx.llm.extract() and returns populated Document | unit | `uv run pytest tests/compiler/documents/test_extract_concepts_pass.py -x` | ❌ Wave 0 |
| LLM-01 | FakeLLMAdapter and PydanticAIAdapter both satisfy LLMPort, swappable via CompilerContext | unit | `uv run pytest tests/llm/test_pydantic_ai_adapter.py tests/compiler/documents/test_extract_concepts_pass.py -x` | ❌ Wave 0 |
| LLM-02 | Cache hit on unchanged document (same 4-key) → no llm.extract() call | unit | `uv run pytest tests/compiler/documents/test_extract_concepts_pass.py::test_cache_hit_skips_extraction -x` | ❌ Wave 0 |
| LLM-02 | Cache key integrity — missing component raises ValueError | unit | `uv run pytest tests/llm/test_cache.py::test_missing_cache_key_component_raises -x` | ❌ Wave 0 |
| LLM-03 | Golden fixture replay — 10 synthetic docs produce expected DocumentExtractionOutput | unit | `uv run pytest tests/compiler/documents/fixtures/extract_concepts/ -x` | ❌ Wave 0 |
| LLM-03 | Zero live API calls in test suite (ALLOW_MODEL_REQUESTS=False) | unit (safety) | `uv run pytest` (autouse fixture blocks calls globally) | ❌ Wave 0 |
| LLM-03 | D-03: extraction failure → Diagnostic, not pipeline halt | unit | `uv run pytest tests/compiler/documents/test_extract_concepts_pass.py::test_extraction_failure_produces_diagnostic -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest -x -q` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/compiler/documents/__init__.py`
- [ ] `tests/compiler/documents/test_parse_pass.py` — covers DOC-01 (section splitting)
- [ ] `tests/compiler/documents/test_section_pass.py` — covers DOC-01 (section normalization)
- [ ] `tests/compiler/documents/test_metadata_pass.py` — covers DOC-01 (metadata fields)
- [ ] `tests/compiler/documents/test_extract_concepts_pass.py` — covers DOC-03, LLM-01, LLM-02, LLM-03 (D-03)
- [ ] `tests/compiler/documents/test_document_compiler.py` — covers DOC-01 (integration), DOC-02 (isolation)
- [ ] `tests/compiler/documents/fixtures/extract_concepts/` — 10 synthetic `.md` + expected output pairs (D-04)
- [ ] `tests/llm/__init__.py`
- [ ] `tests/llm/test_cache.py` — covers LLM-02 (key construction, integrity)
- [ ] `tests/llm/test_prompt_registry.py` — covers prompt versioning
- [ ] `tests/llm/test_pydantic_ai_adapter.py` — covers LLM-01 (adapter satisfies LLMPort)
- [ ] `pyproject.toml` addition: `asyncio_mode = "auto"` under `[tool.pytest.ini_options]`, plus `pytest-asyncio` as dev dep

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` per config.json

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | This is a batch CLI compiler, no user auth |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Single-user CLI tool |
| V5 Input Validation | Yes | Markdown input is untrusted text; pydantic validates all LLM output |
| V6 Cryptography | No | Checksums (SHA) are for change detection, not security — no keys stored |
| V10 Malicious Code | Partial | The LLM extraction pass outputs text extracted from user-supplied docs — no code execution |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| LLM prompt injection via malicious Markdown content | Tampering | Document sections are treated as data (passed as user-turn content), not as instructions. System prompt (`instructions=` on Agent) is fixed and versioned. The extraction prompt must never interpolate raw document text into the system/instructions position. |
| API key leakage via logs or YAML artifacts | Information Disclosure | API keys must come from `Settings(BaseSettings)` reading env vars; never hardcoded in prompt files, pyproject.toml, or YAML artifacts. `pytest-recording` cassettes should filter `Authorization` headers before committing. |
| Path traversal in artifact_id from document filenames | Tampering | Phase 1's `YamlFileRepository` already rejects path-traversal values with `ValueError` — carried forward; document IDs derived from filenames must go through the same validation. |
| Degenerate cache key collision | Tampering | `LLMCacheKey.build()` raises `ValueError` on any empty component — guardrail specified in AI-SPEC.md Section 6 and documented in Pitfall 5 above. |

---

## Sources

### Primary (HIGH confidence)
- [pydantic.dev/docs/ai/core-concepts/output/](https://pydantic.dev/docs/ai/core-concepts/output/) — `output_type`, Tool/Native/Prompted Output modes, ModelRetry, output_validator, retries configuration [fetched 2026-06-30]
- [pydantic.dev/docs/ai/guides/testing/](https://pydantic.dev/docs/ai/guides/testing/) — TestModel, FunctionModel, ALLOW_MODEL_REQUESTS=False, Agent.override(), async test patterns [fetched 2026-06-30]
- [pydantic.dev/docs/ai/api/models/test/](https://pydantic.dev/docs/ai/api/models/test/) — TestModel constructor parameters, call_tools, seed, model_name [fetched 2026-06-30]
- [pypi.org/project/pydantic-ai/](https://pypi.org/project/pydantic-ai/) — v2.1.0, Python 3.10+, current as of 2026-06-30 [VERIFIED]
- [pypi.org/project/markdown-it-py/](https://pypi.org/project/markdown-it-py/) — v4.2.0 (2026-05-07), Python >=3.10, MIT, Google Assured OSS [VERIFIED]
- [pypi.org/project/pytest-recording/](https://pypi.org/project/pytest-recording/) — v0.13.4 (2025-05-08), VCR.py wrapper [VERIFIED]
- `.planning/phases/02-document-compiler/02-CONTEXT.md` — locked decisions D-01 through D-04 [VERIFIED: project docs]
- `.planning/phases/02-document-compiler/02-AI-SPEC.md` — PydanticAI framework quick reference, implementation guidance, evaluation strategy [VERIFIED: project docs, fetched 2026-06-30]
- `.planning/research/ARCHITECTURE.md` — project structure, anti-patterns, pass patterns [VERIFIED: project docs]
- `.planning/research/STACK.md` — technology stack rationale, PydanticAI v1→v2 rename documentation [VERIFIED: project docs]
- Phase 1 source code (`src/kir/core/`, `tests/core/`, `tests/conftest.py`) — actual API surface of existing ports, models, pass registry [VERIFIED: filesystem read 2026-06-30]

### Secondary (MEDIUM confidence)
- [pypi.org/project/pytest-asyncio/](https://pypi.org/project/pytest-asyncio/) — v1.3.0 current; asyncio_mode options [WebSearch verified against PyPI 2026-06-30]
- [github.com/kiwicom/pytest-recording](https://github.com/kiwicom/pytest-recording) — VCR cassette recording/replay, cassette rewrite mode [WebSearch corroborated by PyPI listing]

### Tertiary (LOW confidence)
- None — all critical claims are verified against authoritative sources above.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pydantic-ai and markdown-it-py verified against PyPI; API surface verified against official docs fetched 2026-06-30
- Architecture: HIGH — directly grounded in project's own ARCHITECTURE.md, CONTEXT.md decisions, and Phase 1 source code read
- Pitfalls: HIGH — PydanticAI v2 renames confirmed from official STACK.md + AI-SPEC.md; other pitfalls derived from direct code inspection of Phase 1 contracts
- Test patterns: MEDIUM-HIGH — ALLOW_MODEL_REQUESTS pattern verified from official docs; async mode config needs runtime verification

**Research date:** 2026-06-30
**Valid until:** 2026-07-30 (pydantic-ai is fast-moving in early v2; re-verify output_validator signature and async mode before implementing if > 2 weeks pass)
