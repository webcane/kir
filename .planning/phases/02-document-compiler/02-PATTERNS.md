# Phase 2: Document Compiler — Pattern Map

**Mapped:** 2026-06-30
**Files analyzed:** 18 new/modified files
**Analogs found:** 14 / 18

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/kir/core/ports/llm_port.py` | port (modify) | request-response | `src/kir/core/ports/cache_port.py` | role-match (same Protocol pattern) |
| `src/kir/core/ports/parser_port.py` | port (modify return type) | request-response | `src/kir/core/ports/cache_port.py` | role-match |
| `src/kir/core/domain/models/document.py` | model (modify) | transform | `src/kir/core/domain/ir.py` | exact (add diagnostics field same as FakeIR) |
| `src/kir/core/passes/context.py` | context (modify) | request-response | self | exact (extend frozen dataclass) |
| `src/kir/llm/__init__.py` | package init | — | `src/kir/tooling/__init__.py` | role-match |
| `src/kir/llm/pydantic_ai_adapter.py` | adapter/service | request-response | `src/kir/tooling/repository/yaml_repository.py` | role-match (adapter implementing port) |
| `src/kir/llm/fake_adapter.py` | test-double/adapter | request-response | `tests/core/passes/fakes/fake_llm_port.py` | exact (same fake-port pattern) |
| `src/kir/llm/cache.py` | utility | CRUD | `tests/core/passes/fakes/fake_cache.py` | role-match (builds on CachePort) |
| `src/kir/llm/prompts/__init__.py` | package init | — | `src/kir/tooling/__init__.py` | role-match |
| `src/kir/llm/prompts/registry.py` | utility/registry | request-response | `src/kir/core/passes/registry.py` | role-match (registry pattern) |
| `src/kir/llm/prompts/extract_v1.md` | config/prompt | — | none | no analog |
| `src/kir/compiler/documents/__init__.py` | package init | — | `src/kir/tooling/__init__.py` | role-match |
| `src/kir/compiler/documents/adapters/markdown_it_adapter.py` | adapter | transform | `src/kir/tooling/repository/yaml_repository.py` | role-match (adapter implementing port) |
| `src/kir/compiler/documents/passes/parse.py` | pass | transform | `tests/core/passes/fakes/fake_passes.py` | exact (register_pass decorator + model_copy pattern) |
| `src/kir/compiler/documents/passes/section.py` | pass | transform | `tests/core/passes/fakes/fake_passes.py` | exact |
| `src/kir/compiler/documents/passes/metadata.py` | pass | transform | `tests/core/passes/fakes/fake_passes.py` | exact |
| `src/kir/compiler/documents/passes/extract_concepts.py` | pass (async) | request-response | `tests/core/passes/fakes/fake_passes.py` | role-match (same structure, adds async + error handling) |
| `src/kir/compiler/documents/compiler.py` | service | CRUD | `src/kir/tooling/repository/yaml_repository.py` | role-match (service wiring ports) |
| `tests/conftest.py` | config (modify) | — | self | exact |
| `tests/llm/__init__.py` | test package | — | `tests/core/__init__.py` | role-match |
| `tests/llm/test_cache.py` | test | CRUD | `tests/tooling/repository/test_yaml_repository.py` | role-match |
| `tests/llm/test_prompt_registry.py` | test | request-response | `tests/core/passes/test_registry.py` | role-match |
| `tests/llm/test_pydantic_ai_adapter.py` | test | request-response | `tests/core/passes/test_pipeline_execution.py` | role-match |
| `tests/compiler/documents/` (all test files) | test | transform | `tests/core/passes/test_pipeline_execution.py` | role-match |

---

## Pattern Assignments

### `src/kir/core/ports/llm_port.py` (port, modify)

**Analog:** `src/kir/core/ports/cache_port.py`

**Current file** (full, lines 1-13):
```python
"""LLMPort — domain-owned port for LLM-backed semantic analysis."""
from __future__ import annotations
from typing import Protocol

class LLMPort(Protocol):
    def extract(self, text: str) -> object: ...
```

**Narrowing target — imports pattern** (copy from `src/kir/core/ports/cache_port.py` lines 1-11):
```python
"""CachePort — generic key/value cache port ..."""
from __future__ import annotations
from typing import Protocol
```

**Core Protocol pattern — `cache_port.py` lines 9-11:**
```python
class CachePort(Protocol):
    def get(self, key: str) -> object | None: ...
    def set(self, key: str, value: object) -> None: ...
```

**New shape to implement** (derived from RESEARCH.md Pattern 1):
```python
class ExtractionResult(Protocol):
    """Structural type — satisfied by DocumentExtractionOutput from llm/ package."""
    concepts: list
    glossary: list
    entities: list
    references: list

class LLMPort(Protocol):
    model_id: str

    async def extract(
        self,
        *,
        sections: list[Section],
        prompt: str,
    ) -> ExtractionResult: ...
```

**Import needed:** `from kir.core.domain.models.document import Section`

---

### `src/kir/core/domain/models/document.py` (model, modify)

**Analog:** `src/kir/core/domain/ir.py` (exact match — FakeIR shows the diagnostics field pattern)

**FakeIR diagnostics field pattern** (`src/kir/core/domain/ir.py` lines 1-17):
```python
from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from kir.core.domain.models.diagnostic import Diagnostic

class FakeIR(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    value: int = 0
    diagnostics: tuple[Diagnostic, ...] = ()
```

**Add to `Document` class** (same field pattern, same imports):
```python
from kir.core.domain.models.diagnostic import Diagnostic
# ...
class Document(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    # ... existing fields ...
    diagnostics: tuple[Diagnostic, ...] = ()  # Phase 2: accumulated by extraction pass
```

**Note:** Also update `concepts`, `glossary`, `entities`, `references` from `tuple[str, ...]` to typed tuples once extraction DTOs are defined. Keep defaults `= ()` for backward compatibility with Phase 1 tests.

---

### `src/kir/core/passes/context.py` (context, modify)

**Analog:** self (extend the existing frozen dataclass)

**Current pattern** (`src/kir/core/passes/context.py` lines 23-30):
```python
@dataclass(frozen=True, slots=True)
class CompilerContext:
    llm: LLMPort
    repository: RepositoryPort
    parser: MarkdownParserPort
    compiler_version: str
    schema_version: str
```

**Phase 2 additions** (RESEARCH.md Open Question 3 — extend directly):
```python
# New imports to add:
from kir.core.ports.cache_port import CachePort

@dataclass(frozen=True, slots=True)
class CompilerContext:
    llm: LLMPort
    repository: RepositoryPort
    parser: MarkdownParserPort
    compiler_version: str
    schema_version: str
    # Phase 2 additions:
    prompt_version: str = ""        # threaded from core/config/versions.py
    llm_cache: CachePort | None = None   # generic cache; LLM key construction in llm/cache.py
    prompts: object = None          # PromptRegistry instance (typed as object to avoid llm/ import)
```

**Note:** `prompts` typed as `object` to avoid importing `PromptRegistry` (which lives in `llm/`) into `core/`. Pass code accesses it via `ctx.prompts.render(...)` — structural duck-typing, consistent with existing Protocol-typing approach.

---

### `src/kir/llm/pydantic_ai_adapter.py` (adapter, request-response)

**Analog:** `src/kir/tooling/repository/yaml_repository.py` (adapter implementing a port)

**Adapter constructor pattern** (`yaml_repository.py` lines 26-29):
```python
class YamlFileRepository:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir
        self._yaml = ruamel.yaml.YAML(typ="safe")
```

**Core adapter pattern — `yaml_repository.py` lines 38-47:**
```python
def save(self, artifact_id: str, artifact: object) -> None:
    self._validate_artifact_id(artifact_id)
    self._dir.mkdir(parents=True, exist_ok=True)
    with open(self._dir / f"{artifact_id}.yaml", "w") as f:
        self._yaml.dump(artifact, f)
```

**PydanticAI-specific implementation** (from RESEARCH.md Pattern 2 — the only file that imports `pydantic_ai`):
```python
from __future__ import annotations
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.settings import ModelSettings
# DocumentExtractionOutput defined in same file as the DTO

class DocumentExtractionOutput(BaseModel):
    """Combined extraction DTO — returned by LLMPort.extract(), stored in LLM cache."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    concepts: tuple[str, ...] = ()
    glossary: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    references: tuple[str, ...] = ()

class PydanticAIAdapter:
    model_id: str  # satisfies LLMPort.model_id

    def __init__(self, model: str, *, max_output_retries: int = 2):
        self.model_id = model
        self._agent = Agent(
            model,
            output_type=DocumentExtractionOutput,  # v2 API: output_type not result_type
            model_settings=ModelSettings(temperature=0.1, max_tokens=4096),
        )
        # output_validator for semantic non-empty check (RESEARCH.md Pattern 2)
        @self._agent.output_validator
        async def _non_empty(output: DocumentExtractionOutput) -> DocumentExtractionOutput:
            if not any([output.concepts, output.glossary, output.entities, output.references]):
                raise ModelRetry("All four extraction categories are empty — re-read and retry.")
            return output

    async def extract(self, *, sections, prompt: str) -> DocumentExtractionOutput:
        result = await self._agent.run(prompt)
        return result.output  # v2 API: .output not .data
```

---

### `src/kir/llm/fake_adapter.py` (test-double, request-response)

**Analog:** `tests/core/passes/fakes/fake_llm_port.py` (exact — same fake-port pattern)

**Existing fake pattern** (`fake_llm_port.py` lines 1-8):
```python
"""FakeLLMPort — trivial, no-network implementation of LLMPort for tests."""
from __future__ import annotations

class FakeLLMPort:
    def extract(self, text: str) -> object:
        return {"text": text}
```

**Phase 2 extension** (adds `model_id`, `call_count`, configurable output, async):
```python
"""FakeLLMAdapter — production-tree fake satisfying LLMPort for DI and golden-fixture tests."""
from __future__ import annotations
from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput

class FakeLLMAdapter:
    model_id: str = "fake:v0"

    def __init__(self, output: DocumentExtractionOutput | None = None):
        self._output = output or DocumentExtractionOutput()
        self._call_count = 0

    async def extract(self, *, sections, prompt: str) -> DocumentExtractionOutput:
        self._call_count += 1
        return self._output

    @property
    def call_count(self) -> int:
        return self._call_count
```

---

### `src/kir/llm/cache.py` (utility, CRUD)

**Analog:** `tests/core/passes/fakes/fake_cache.py` (builds on the same CachePort Protocol)

**FakeCache pattern** (`fake_cache.py` lines 1-17):
```python
from __future__ import annotations

class FakeCache:
    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._store.get(key)

    def set(self, key: str, value: object) -> None:
        self._store[key] = value
```

**LLM-specific cache-key layer** (from RESEARCH.md Pattern 3):
```python
from __future__ import annotations
from kir.core.ports.cache_port import CachePort

class LLMCacheKey:
    def build(self, checksum: str, prompt_version: str, schema_version: str, model_id: str) -> str:
        if not all([checksum, prompt_version, schema_version, model_id]):
            raise ValueError("All four cache key components must be non-empty (LLM-02 integrity)")
        return f"{checksum}:{prompt_version}:{schema_version}:{model_id}"

class LLMCache:
    def __init__(self, backend: CachePort):
        self._backend = backend
        self._key_builder = LLMCacheKey()

    def get(self, checksum, prompt_version, schema_version, model_id):
        return self._backend.get(self._key_builder.build(checksum, prompt_version, schema_version, model_id))

    def set(self, checksum, prompt_version, schema_version, model_id, value):
        self._backend.set(self._key_builder.build(checksum, prompt_version, schema_version, model_id), value)
```

**InMemoryCache** (production CachePort impl for Phase 2 — Pattern 7 from RESEARCH.md):
```python
class InMemoryCache:
    """Production in-memory CachePort for Phase 2. File-based cache is Phase 5 scope."""
    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._store.get(key)

    def set(self, key: str, value: object) -> None:
        self._store[key] = value
```

---

### `src/kir/llm/prompts/registry.py` (utility/registry, request-response)

**Analog:** `src/kir/core/passes/registry.py` (registry pattern with validation)

**Registry error pattern** (`registry.py` lines 18-22):
```python
class MissingDependencyError(ValueError):
    """Raised at pipeline() build time when a pass declares depends_on
    naming a pass that was never registered."""
```

**PromptRegistry pattern** (load prompt file by name + version; raise loudly on missing):
```python
from __future__ import annotations
from pathlib import Path

class PromptNotFoundError(FileNotFoundError):
    """Raised when a requested prompt name+version has no corresponding file."""

class PromptRegistry:
    def __init__(self, prompts_dir: Path | None = None):
        self._dir = prompts_dir or Path(__file__).parent

    def render(self, name: str, **kwargs: object) -> str:
        """Load versioned prompt template and interpolate kwargs."""
        # name = "extract_v1" → file = prompts/extract_v1.md
        path = self._dir / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(f"Prompt template not found: {path}")
        template = path.read_text(encoding="utf-8")
        return template.format(**kwargs)
```

---

### `src/kir/compiler/documents/adapters/markdown_it_adapter.py` (adapter, transform)

**Analog:** `src/kir/tooling/repository/yaml_repository.py` (adapter implementing a port; the only file importing the third-party library)

**Adapter boundary pattern** (`yaml_repository.py` lines 14-30):
```python
"""YamlFileRepository — the project's first permanent adapter ...
Per the Phase 1 threat register ...: `artifact_id` is the only
externally-influenced input this phase that becomes a filesystem path
component, so it is validated ..."""

from __future__ import annotations
import re
from pathlib import Path
import ruamel.yaml

class YamlFileRepository:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir
        self._yaml = ruamel.yaml.YAML(typ="safe")
```

**MarkdownIt adapter shape** (the only file importing `markdown_it`; returns `list[Section]` — a domain type — so no pass ever sees `markdown_it` types):
```python
from __future__ import annotations
from markdown_it import MarkdownIt
from kir.core.domain.models.document import Section

class MarkdownItAdapter:
    def __init__(self) -> None:
        self._md = MarkdownIt()

    def parse(self, text: str) -> list[Section]:
        """Parse Markdown text into Sections at every heading (H1-H6).
        Content before the first heading → preamble section with heading=''."""
        tokens = self._md.parse(text)
        # ... heading-based splitting logic using token.type == "heading_open" ...
        return sections
```

**Critical:** Return type is `list[Section]` (domain type), not `markdown_it.Token`. This satisfies `MarkdownParserPort` structurally and keeps passes free of `markdown_it` imports.

---

### `src/kir/compiler/documents/passes/parse.py`, `section.py`, `metadata.py` (pass, transform)

**Analog:** `tests/core/passes/fakes/fake_passes.py` (exact — defines the canonical register_pass + model_copy pattern)

**Register-pass decorator pattern** (`fake_passes.py` lines 19-28):
```python
from kir.core.passes.registry import PassRegistry

registry = PassRegistry()

def register_pass(name: str, depends_on: tuple[str, ...] = ()):
    def decorator(fn):
        fn.name = name
        fn.depends_on = depends_on
        registry.register(fn)
        return fn
    return decorator

@register_pass("fake_a")
def fake_pass_a(ir: FakeIR, ctx: object) -> FakeIR:
    ...
```

**Immutable IR update pattern** (`fake_passes.py` lines 30-43):
```python
@register_pass("fake_a")
def fake_pass_a(ir: FakeIR, ctx: object) -> FakeIR:
    return ir.model_copy(
        update={
            "value": ir.value + 1,
            "diagnostics": ir.diagnostics + (
                Diagnostic(code="FAKE_A", severity=Severity.INFO, message="fake_pass_a ran"),
            ),
        }
    )
```

**Dependency declaration pattern** (`fake_passes.py` lines 46-58):
```python
@register_pass("fake_b", depends_on=("fake_a",))
def fake_pass_b(ir: FakeIR, ctx: object) -> FakeIR:
    return ir.model_copy(update={"value": ir.value + 1, ...})
```

**Document pass shape** (adapts the fake pass pattern to Document IR):
```python
# parse.py
from __future__ import annotations
from kir.core.domain.models.document import Document, Section
from kir.core.passes.context import CompilerContext
# (registry instance defined in compiler/documents/passes/__init__.py or a module-level one)

@register_pass("parse")
def parse_pass(ir: Document, ctx: CompilerContext) -> Document:
    sections: list[Section] = ctx.parser.parse(ir.source)  # adapter call via port
    return ir.model_copy(update={"sections": tuple(sections)})
```

**Note:** Each pass file imports from `kir.core` only — never from `kir.llm` or other passes directly.

---

### `src/kir/compiler/documents/passes/extract_concepts.py` (pass async, request-response)

**Analog:** `tests/core/passes/fakes/fake_passes.py` (role-match; adds async + cache + error handling)

**Diagnostic accumulation pattern** (`fake_passes.py` lines 30-43) — already shown above.

**Async pass with D-03 failure handling** (from RESEARCH.md Pattern 4):
```python
from __future__ import annotations
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

**Critical:** `async def` — never `run_sync()`. Model_copy, not mutation. Exception catch covers exhausted retries (D-03).

---

### `src/kir/compiler/documents/compiler.py` (service, CRUD)

**Analog:** `src/kir/tooling/repository/yaml_repository.py` (service that wires dependencies)

**Constructor/wiring pattern** (`yaml_repository.py` lines 26-29):
```python
class YamlFileRepository:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir
        self._yaml = ruamel.yaml.YAML(typ="safe")
```

**DocumentCompiler wiring** (orchestrates PassRegistry pipeline, threads CompilerContext):
```python
from __future__ import annotations
from pathlib import Path
from kir.core.passes.context import CompilerContext
from kir.core.passes.registry import PassRegistry
from kir.core.domain.models.document import Document

class DocumentCompiler:
    def __init__(self, registry: PassRegistry, context: CompilerContext) -> None:
        self._pipeline = registry.pipeline()  # validated at construction time
        self._ctx = context

    async def compile(self, source_path: Path) -> Document:
        """Compile a single Markdown file into a Document IR."""
        text = source_path.read_text(encoding="utf-8")
        ir = Document(id=..., title="", source=text, checksum=..., language="en")
        for pass_fn in self._pipeline:
            ir = await pass_fn(ir, self._ctx) if asyncio.iscoroutinefunction(pass_fn) else pass_fn(ir, self._ctx)
        return ir
```

---

### `tests/conftest.py` (config, modify)

**Analog:** self (existing conftest extended with Phase 2 fixtures)

**Existing fixture pattern** (`tests/conftest.py` lines 23-33):
```python
@pytest.fixture
def fake_compiler_context() -> CompilerContext:
    return CompilerContext(
        llm=FakeLLMPort(),
        repository=InMemoryFakeRepository(),
        parser=FakeMarkdownParser(),
        compiler_version=compiler_version,
        schema_version=schema_version,
    )
```

**Phase 2 additions** (from RESEARCH.md Pattern 5):
```python
# Add to tests/conftest.py:
from pydantic_ai import models as pydantic_ai_models

@pytest.fixture(autouse=True)
def block_real_llm_calls():
    """Ensure zero live API calls in CI — LLM-03."""
    original = pydantic_ai_models.ALLOW_MODEL_REQUESTS
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = False
    yield
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = original
```

**Also add to `pyproject.toml` `[tool.pytest.ini_options]`:**
```toml
asyncio_mode = "auto"
```

---

### Test files: `tests/compiler/documents/` and `tests/llm/` (tests)

**Analog:** `tests/tooling/repository/test_yaml_repository.py` and `tests/core/passes/test_pipeline_execution.py`

**Test structure pattern** (`test_yaml_repository.py` lines 1-18):
```python
from __future__ import annotations
from pathlib import Path
import pytest
from kir.tooling.repository.yaml_repository import YamlFileRepository

def test_save_then_load_roundtrips(tmp_path: Path) -> None:
    repo = YamlFileRepository(tmp_path / "kir")
    repo.save("artifact-1", {"id": "artifact-1", "version": 1})
    assert repo.load("artifact-1") == {"id": "artifact-1", "version": 1}
```

**Pipeline test pattern** (`test_pipeline_execution.py` lines 22-34):
```python
def test_pipeline_executes_passes_in_dependency_order_and_accumulates_diagnostics(
    fake_registry: PassRegistry, fake_compiler_context: CompilerContext
) -> None:
    pipeline = fake_registry.pipeline()
    result = FakeIR(value=0)
    for pass_fn in pipeline:
        result = pass_fn(result, fake_compiler_context)
    assert result.value == 2
    assert len(result.diagnostics) >= 2
```

**Async test shape** (needed for `ExtractConceptsPass` and `PydanticAIAdapter` tests — per `asyncio_mode = "auto"` in pyproject.toml):
```python
# No @pytest.mark.asyncio needed when asyncio_mode = "auto"
async def test_extract_concepts_pass_calls_llm(fake_document_compiler_context):
    ir = make_document_with_sections()
    result = await extract_concepts_pass(ir, fake_document_compiler_context)
    assert fake_document_compiler_context.llm.call_count == 1
    assert len(result.concepts) > 0
```

---

## Shared Patterns

### Immutable IR Updates
**Source:** `tests/core/passes/fakes/fake_passes.py` lines 30-43
**Apply to:** All four document passes (`parse.py`, `section.py`, `metadata.py`, `extract_concepts.py`)
```python
return ir.model_copy(update={"field": new_value})
# Never: ir.field = new_value  (frozen=True forbids mutation)
```

### `from __future__ import annotations` Header
**Source:** Every existing source file (e.g., `src/kir/core/ports/cache_port.py` line 7, `src/kir/core/domain/models/document.py` line 7)
**Apply to:** All new Python files
```python
from __future__ import annotations
```

### Frozen Pydantic Model Config
**Source:** `src/kir/core/domain/models/document.py` lines 23-24
**Apply to:** `DocumentExtractionOutput` DTO in `pydantic_ai_adapter.py`, any new domain models
```python
model_config = ConfigDict(frozen=True, extra="forbid")
```

### Adapter Docstring Boundary Declaration
**Source:** `src/kir/tooling/repository/yaml_repository.py` lines 1-14
**Apply to:** `markdown_it_adapter.py`, `pydantic_ai_adapter.py`
```
"""AdapterName — the only file that imports <third-party-lib>.
Per the hexagonal boundary: <domain> must never import <third-party-lib>."""
```

### Port-as-Protocol Pattern
**Source:** `src/kir/core/ports/cache_port.py` lines 1-11
**Apply to:** Any new narrowed port shapes in `llm_port.py`, `parser_port.py`
```python
from __future__ import annotations
from typing import Protocol

class SomePort(Protocol):
    def method(self, ...) -> ...: ...
```

### Diagnostic Accumulation (D-03)
**Source:** `tests/core/passes/fakes/fake_passes.py` lines 30-43 + `src/kir/core/domain/ir.py` lines 16-17
**Apply to:** `extract_concepts.py` error handling; `Document` model (add `diagnostics` field)
```python
diagnostics: tuple[Diagnostic, ...] = ()
# In a pass:
return ir.model_copy(update={
    "diagnostics": ir.diagnostics + (Diagnostic(code=..., severity=..., message=...), )
})
```

### Pass Registration (Decorator Must Fire at Import)
**Source:** `tests/core/passes/fakes/fake_passes.py` lines 19-28 + RESEARCH.md Pitfall 3
**Apply to:** All four passes; `compiler/documents/passes/__init__.py`
```python
# compiler/documents/passes/__init__.py must explicitly import all pass modules:
from . import parse, section, metadata, extract_concepts
```

### `tmp_path` Fixture for File I/O Tests
**Source:** `tests/tooling/repository/test_yaml_repository.py` lines 15-18
**Apply to:** `test_document_compiler.py` (end-to-end .md → Document IR test)
```python
def test_...(tmp_path: Path) -> None:
    # Write synthetic .md to tmp_path, compile, assert Document IR fields
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/kir/llm/prompts/extract_v1.md` | prompt template | — | No prompt files exist; format is new to this project |
| `tests/compiler/documents/fixtures/extract_concepts/` | test fixtures | — | No golden fixture corpora exist; hand-authored per D-04 |

---

## Metadata

**Analog search scope:** `src/kir/`, `tests/`
**Files scanned:** 28 source + test files
**Pattern extraction date:** 2026-06-30
