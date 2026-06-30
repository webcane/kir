# Phase 1: Compiler Foundation - Pattern Map

**Mapped:** 2026-06-30
**Files analyzed:** 18 (domain models, ports, passes mechanics, tooling, tests)
**Analogs found:** 0 in-repo / 18 via research-provided reference implementations

## No In-Repo Code Exists

This is a greenfield repository: no `src/` directory, no `pyproject.toml`, no prior Python source of any kind (confirmed via `ls`/`find` on the repo root — only `CLAUDE.md`, `LICENSE`, `README.md` exist at the top level). There are **zero in-repo analogs** to search for or extract patterns from.

In place of in-repo analogs, this PATTERNS.md treats the concrete code sketches in `.planning/research/ARCHITECTURE.md` (Pattern 1/2/3) and `.planning/phases/01-compiler-foundation/01-RESEARCH.md` (the closed `graphlib`-based `pipeline()` implementation, Pydantic frozen-model patterns, Protocol-based port definitions) as the canonical reference implementations every new file in this phase should follow. These are not "closest analogs found by search" — they are the project's own pre-approved design, already vetted in CONTEXT.md's decisions (D-01..D-04) and RESEARCH.md's Architecture Patterns section. Treat them as load-bearing source, not inspiration.

## File Classification

| New File | Role | Data Flow | Reference Pattern | Source |
|----------|------|-----------|--------------------|--------|
| `src/kir/core/domain/models/document.py` | model | transform | Pattern 2 (frozen Pydantic model) | RESEARCH.md Pattern 2 |
| `src/kir/core/domain/models/concept.py` | model | transform | Pattern 2 (frozen Pydantic model) | RESEARCH.md Pattern 2 |
| `src/kir/core/domain/models/relation.py` | model | transform | Pattern 2 (frozen Pydantic model) | RESEARCH.md Pattern 2 |
| `src/kir/core/domain/models/taxonomy.py` | model | transform | Pattern 2 (frozen Pydantic model) | RESEARCH.md Pattern 2 |
| `src/kir/core/domain/models/conflict.py` | model | transform | Pattern 2 (frozen Pydantic model) | RESEARCH.md Pattern 2 (scope: see Open Question A3) |
| `src/kir/core/domain/models/provenance.py` | model | transform | Pattern 2 (frozen Pydantic model, value object) | RESEARCH.md Pattern 2 |
| `src/kir/core/domain/models/diagnostic.py` | model | transform | Pattern 2 (frozen Pydantic model + enum) | RESEARCH.md Code Examples (`Diagnostic`/`Severity`) |
| `src/kir/core/domain/value_objects.py` | model | transform | Pattern 2 (frozen Pydantic model, value objects) | RESEARCH.md Pattern 2 |
| `src/kir/core/domain/manifest.py` | model | CRUD (minimal: id+version) | Pattern 2 (frozen Pydantic model) | RESEARCH.md Pattern 2; D-04 scope limit |
| `src/kir/core/domain/ir.py` | model | transform | Pattern 2 `FakeIR` sketch | RESEARCH.md Pattern 2 (`FakeIR` example) |
| `src/kir/core/ports/llm_port.py` | service (port) | request-response | Pattern 3 (`Protocol` port) | RESEARCH.md Pattern 3 |
| `src/kir/core/ports/repository_port.py` | service (port) | CRUD | Pattern 3 (`RepositoryPort` Protocol) | RESEARCH.md Pattern 3, exact sketch given |
| `src/kir/core/ports/parser_port.py` | service (port) | transform | Pattern 3 (`Protocol` port) | RESEARCH.md Pattern 3 |
| `src/kir/core/ports/cache_port.py` | service (port) | CRUD (generic KV) | Pattern 3 (`Protocol` port); D-03 scope limit | RESEARCH.md Pattern 3 |
| `src/kir/core/passes/base.py` | middleware (contract) | event-driven (pipeline step) | Pattern 1 `Pass` Protocol | RESEARCH.md Pattern 1, exact sketch given |
| `src/kir/core/passes/registry.py` | service | event-driven (dependency-ordered dispatch) | Pattern 1 `PassRegistry` (full impl, closes RESEARCH.md's "comment-only" gap) | RESEARCH.md Pattern 1, exact sketch given |
| `src/kir/core/passes/context.py` | config/provider | request-response (DI container) | Open Question 1 recommendation: frozen `dataclass` | RESEARCH.md Standard Stack / Alternatives Considered, Open Questions §1 |
| `src/kir/core/config/versions.py` | config | n/a (constants) | No sketch provided — plain module-level constants | RESEARCH.md Recommended Project Structure |
| `src/kir/tooling/repository/yaml_repository.py` | service (adapter) | file-I/O | Pattern 3 `YamlFileRepository` (variant 2) | RESEARCH.md Pattern 3, exact sketch given |
| `tests/core/passes/fakes/fake_passes.py` | test | event-driven | Pattern 1 (`register_pass` decorator + two fake passes) | RESEARCH.md Pattern 1, exact sketch given |
| `tests/core/passes/fakes/fake_llm_port.py` | test | request-response | Pattern 3 (fake port implementation) | RESEARCH.md Pattern 3 (apply same style as `InMemoryFakeRepository`) |
| `tests/core/passes/fakes/fake_repository.py` | test | CRUD | Pattern 3 `InMemoryFakeRepository` (variant 1) | RESEARCH.md Pattern 3, exact sketch given |
| `tests/core/passes/fakes/fake_parser.py` | test | transform | Pattern 3 (fake port implementation) | RESEARCH.md Pattern 3 (apply same style as `InMemoryFakeRepository`) |
| `tests/core/test_import_boundaries.py` | test | static analysis | Code Examples: CORE-01 import audit | RESEARCH.md Code Examples, exact sketch given |
| `tests/core/passes/test_registry.py` | test | event-driven | Code Examples: D-02 build-time error tests | RESEARCH.md Code Examples, exact sketch given |
| `tests/core/passes/test_pipeline_execution.py` | test | event-driven | Code Examples: byte-identical rerun proof | RESEARCH.md Code Examples, exact sketch given |
| `tests/core/test_repository_port_contract.py` | test | CRUD | Pattern 3: parametrized contract test across both fakes | RESEARCH.md Pattern 3, exact sketch given |
| `tests/tooling/repository/test_yaml_repository.py` | test | file-I/O | Pattern 3 (contract test against `YamlFileRepository`) | RESEARCH.md Pattern 3 |

## Pattern Assignments

### `src/kir/core/passes/registry.py` (service, event-driven)

**Reference:** `.planning/phases/01-compiler-foundation/01-RESEARCH.md`, "Pattern 1: Decorator-Based Self-Registration with Build-Time Topological Sort" (lines 236-280)

**This is the single most load-bearing excerpt in the phase** — RESEARCH.md explicitly flags that ARCHITECTURE.md's own sketch left `pipeline()`'s body as a comment (`# topological sort over depends_on`), and this is the closed, real implementation that must be copied verbatim (not reinvented):

```python
# core/passes/registry.py
from __future__ import annotations
from graphlib import TopologicalSorter, CycleError
from typing import Protocol

class Pass(Protocol):
    name: str
    depends_on: tuple[str, ...]
    def __call__(self, ir: object, ctx: "CompilerContext") -> object: ...

class MissingDependencyError(ValueError):
    """Raised at pipeline() build time when a pass declares depends_on
    naming a pass that was never registered. Per D-02, this is NOT
    raised at register_pass() time."""

class PassRegistry:
    def __init__(self) -> None:
        self._passes: dict[str, Pass] = {}

    def register(self, pass_obj: Pass) -> Pass:
        # Registration itself never validates depends_on (D-02) —
        # import order may mean a dependency hasn't registered yet.
        self._passes[pass_obj.name] = pass_obj
        return pass_obj

    def pipeline(self) -> list[Pass]:
        graph: dict[str, set[str]] = {}
        for name, p in self._passes.items():
            for dep in p.depends_on:
                if dep not in self._passes:
                    raise MissingDependencyError(
                        f"Pass {name!r} declares depends_on={dep!r}, "
                        f"but no pass named {dep!r} is registered."
                    )
            graph[name] = set(p.depends_on)
        try:
            sorter = TopologicalSorter(graph)
            ordered_names = list(sorter.static_order())
        except CycleError as exc:
            # exc.args[1] is the list of nodes forming the cycle (CPython docs)
            raise CycleError(
                f"Circular pass dependency detected: {exc.args[1]}"
            ) from exc
        return [self._passes[name] for name in ordered_names]
```

**Key rule (D-02):** `register()` must never validate `depends_on` — only `pipeline()` does, at build time.

---

### `tests/core/passes/fakes/fake_passes.py` (test, event-driven)

**Reference:** RESEARCH.md Pattern 1 (lines 282-303)

```python
# tests/core/passes/fakes/fake_passes.py
from core.passes.registry import PassRegistry

test_registry = PassRegistry()

def register_pass(name: str, depends_on: tuple[str, ...] = ()):
    def decorator(fn):
        fn.name = name
        fn.depends_on = depends_on
        test_registry.register(fn)
        return fn
    return decorator

@register_pass("fake_a")
def fake_pass_a(ir, ctx):
    return ir.model_copy(update={"diagnostics": ir.diagnostics + (...,)})

@register_pass("fake_b", depends_on=("fake_a",))
def fake_pass_b(ir, ctx):
    return ir.model_copy(update={...})
```

**Pitfall to encode in `__init__.py`:** decorators only fire on import — must have an explicit `tests/core/passes/fakes/__init__.py` importing every fake-pass module (RESEARCH.md Pitfall 1, lines 426-430).

---

### `src/kir/core/domain/models/diagnostic.py` (model, transform)

**Reference:** RESEARCH.md Pattern 2 (lines 314-331) and Code Examples

```python
# core/domain/models/diagnostic.py
from enum import Enum
from pydantic import BaseModel, ConfigDict

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Diagnostic(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str
    severity: Severity
    message: str
    location: str | None = None      # e.g. source ref — SourceRef VO once real passes exist
    suggestion: str | None = None
```

**Apply to ALL domain/IR models in this phase** (Document, Concept, Relation, Taxonomy, Conflict, Provenance, ArtifactManifest, value objects):
- `model_config = ConfigDict(frozen=True)` on every model
- Per the Security Domain section of RESEARCH.md, also add `extra="forbid"` to every domain/IR model: `ConfigDict(frozen=True, extra="forbid")`
- Use `tuple[...]`, never `list[...]`, for any accumulating field (e.g. `diagnostics: tuple[Diagnostic, ...] = ()`) — a `list` field on a frozen model is still internally mutable via `.append()`, which silently violates CORE-07
- Never add `@cached_property` to a frozen IR model field — `model_copy()` copies the stale cached value (Pydantic issue #11955, cited in RESEARCH.md Pattern 2)

**Fake IR for pass-mechanics tests** (a separate, minimal type — do not reuse Document/Concept for registry plumbing tests, per Open Question 3's recommendation):

```python
class FakeIR(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: int = 0
    diagnostics: tuple[Diagnostic, ...] = ()   # tuple, not list
```

---

### `src/kir/core/ports/repository_port.py` (service/port, CRUD)

**Reference:** RESEARCH.md Pattern 3 (lines 352-359)

```python
# core/ports/repository_port.py
from typing import Protocol

class RepositoryPort(Protocol):
    def save(self, artifact_id: str, artifact: object) -> None: ...
    def load(self, artifact_id: str) -> object: ...
```

**Apply the same `Protocol` shape to `LLMPort`, `MarkdownParserPort`, `CachePort`** — structural typing, no inheritance required of adapters. Do not use `@runtime_checkable` + `isinstance()` as the primary test strategy (Anti-Pattern, RESEARCH.md lines 409).

---

### `tests/core/passes/fakes/fake_repository.py` + `src/kir/tooling/repository/yaml_repository.py` (test / adapter, CRUD + file-I/O)

**Reference:** RESEARCH.md Pattern 3 (lines 361-403) — two interchangeable fakes proven against ONE shared contract test, which is the actual proof of port-substitutability (a single hand-written fake without a contract test only proves "a fake exists," not "the boundary is real"):

```python
# tests/core/passes/fakes/fake_repository.py — variant 1
class InMemoryFakeRepository:
    def __init__(self) -> None:
        self._store: dict[str, object] = {}
    def save(self, artifact_id: str, artifact: object) -> None:
        self._store[artifact_id] = artifact
    def load(self, artifact_id: str) -> object:
        return self._store[artifact_id]

# tests/tooling/repository/yaml_repository.py — variant 2 (test-scoped real)
import ruamel.yaml
from pathlib import Path

class YamlFileRepository:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir
        self._yaml = ruamel.yaml.YAML(typ="safe")
    def save(self, artifact_id: str, artifact: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._dir / f"{artifact_id}.yaml", "w") as f:
            self._yaml.dump(artifact, f)
    def load(self, artifact_id: str) -> dict:
        with open(self._dir / f"{artifact_id}.yaml") as f:
            return self._yaml.load(f)
```

```python
# tests/core/test_repository_port_contract.py — shared contract test, run against BOTH fakes
import pytest

@pytest.fixture(params=["in_memory", "yaml_file"])
def repository(request, tmp_path):
    if request.param == "in_memory":
        return InMemoryFakeRepository()
    return YamlFileRepository(tmp_path / "kir")

def test_save_then_load_roundtrips(repository):
    repository.save("artifact-1", {"id": "artifact-1", "version": 1})
    assert repository.load("artifact-1") == {"id": "artifact-1", "version": 1}
```

**Note on Open Question 2 (RESEARCH.md):** `YamlFileRepository` should be built as the real, permanent adapter under `tooling/repository/`, not throwaway scaffolding — STOR-01/STOR-02's success criteria explicitly require proof against real filesystem I/O ("produces one individual YAML file per artifact... in a directory verifiably separate from raw source"), not an in-memory simulation.

**Security note to carry into implementation:** sanitize `artifact_id` before using it to construct a filesystem path (no raw user/LLM-controlled text, derive from slug/UUID) — `pathlib.Path` does not auto-prevent `..` traversal (RESEARCH.md Security Domain, path traversal row).

---

### `tests/core/test_import_boundaries.py` (test, static analysis)

**Reference:** RESEARCH.md Code Examples, "CORE-01 Import Boundary Verification Test" (lines 452-482) — copy verbatim, this is the exact enforcement mechanism for CLAUDE.md's "Layer Boundaries" rule:

```python
# tests/core/test_import_boundaries.py
import ast
from pathlib import Path

FORBIDDEN_MODULES = {
    "yaml", "ruamel", "openai", "anthropic", "pydantic_ai",
    "pathlib", "os.path", "requests", "httpx", "markdown_it", "mistune",
}

def _imported_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules

def test_domain_has_no_forbidden_imports():
    domain_files = Path("src/kir/core/domain").rglob("*.py")
    violations = {}
    for f in domain_files:
        found = _imported_modules(f) & FORBIDDEN_MODULES
        if found:
            violations[str(f)] = found
    assert not violations, f"Forbidden imports in domain layer: {violations}"
```

---

### `tests/core/passes/test_registry.py` (test, event-driven)

**Reference:** RESEARCH.md Code Examples, "D-02 Build-Time Error Detection Proof" (lines 504-524) — copy verbatim, proves the registration-never-validates / pipeline-always-validates contract:

```python
# tests/core/passes/test_registry.py
from graphlib import CycleError
from core.passes.registry import PassRegistry, MissingDependencyError

def test_missing_dependency_detected_at_pipeline_build_time():
    registry = PassRegistry()
    registry.register(_fake_pass("a", depends_on=("nonexistent",)))
    # Registration itself must NOT raise (D-02):
    with pytest.raises(MissingDependencyError, match="nonexistent"):
        registry.pipeline()

def test_circular_dependency_detected_at_pipeline_build_time():
    registry = PassRegistry()
    registry.register(_fake_pass("a", depends_on=("b",)))
    registry.register(_fake_pass("b", depends_on=("a",)))
    with pytest.raises(CycleError):
        registry.pipeline()
```

---

### `tests/core/passes/test_pipeline_execution.py` (test, event-driven)

**Reference:** RESEARCH.md Code Examples, "Byte-Identical Rerun Proof" (lines 484-502) — proves CORE-04/D-01's "always run every pass, accumulate diagnostics, never halt mid-run" contract plus determinism:

```python
# tests/core/passes/test_pipeline_execution.py
def test_rerun_produces_byte_identical_output(fake_registry, fake_compiler_context):
    initial_ir = FakeIR(value=0)

    pipeline = fake_registry.pipeline()
    result_1 = initial_ir
    for pass_fn in pipeline:
        result_1 = pass_fn(result_1, fake_compiler_context)

    result_2 = initial_ir
    for pass_fn in pipeline:
        result_2 = pass_fn(result_2, fake_compiler_context)

    assert result_1.model_dump_json() == result_2.model_dump_json()
    # Also verify diagnostics are present and structured, not printed:
    assert all(isinstance(d, Diagnostic) for d in result_1.diagnostics)
```

**Determinism pitfall to guard against (RESEARCH.md Pitfall 2):** non-deterministic `set`/unsorted-`dict`-merge iteration anywhere diagnostics or manifest entries are accumulated — `dict` insertion order is fine in CPython, `set` over pass names or merged registries is not. Sort explicitly by stable key wherever this risk exists.

---

### `src/kir/core/passes/context.py` (config/provider, request-response)

**No code sketch given in research** — this is an explicit design decision the planner must make, not a literal excerpt to copy. Per RESEARCH.md's Open Question 1 / Alternatives Considered:

**Recommendation:** Use `dataclass(frozen=True, slots=True)`, NOT a Pydantic `BaseModel`, because `CompilerContext` holds `Protocol`-typed port fields (`llm: LLMPort`, `repository: RepositoryPort`) that are not natively Pydantic-validatable without `ConfigDict(arbitrary_types_allowed=True)`, and `CompilerContext` is never serialized/persisted (unlike the IR types, which should remain Pydantic per CLAUDE.md's "Explicit Pydantic models over dicts").

```python
# core/passes/context.py — shape only, not a verbatim sketch from research
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class CompilerContext:
    llm: "LLMPort"
    repository: "RepositoryPort"
    parser: "MarkdownParserPort"
    compiler_version: str
    schema_version: str
```

**Constraint from CLAUDE.md "No global state":** `CompilerContext` must always be constructed explicitly by the caller (test code this phase) and passed into every pass call — never read from a module-level global. (Contrast with `PassRegistry`, which IS sanctioned as module-level state per RESEARCH.md's explicit caveat, lines 36.)

## Shared Patterns

### Frozen + forbid-extra Pydantic config (CORE-07, ASVS V5)
**Source:** RESEARCH.md Pattern 2 + Security Domain
**Apply to:** every file under `src/kir/core/domain/models/`, `value_objects.py`, `manifest.py`, `ir.py`
```python
model_config = ConfigDict(frozen=True, extra="forbid")
```
Use `model_copy(update={...})` for all transformations; never direct field assignment. Use `tuple[...]` not `list[...]` for accumulating fields.

### Protocol-based ports, no inheritance
**Source:** RESEARCH.md Pattern 3
**Apply to:** all four files under `src/kir/core/ports/`
Define as `typing.Protocol` subclasses with method signatures only; adapters/fakes satisfy structurally. Avoid `@runtime_checkable` + `isinstance()` as the primary verification strategy — prefer functional contract tests (see `test_repository_port_contract.py` pattern) run against 2+ fakes per port.

### Build-time-only dependency validation (D-02)
**Source:** RESEARCH.md Pattern 1 / `PassRegistry`
**Apply to:** `registry.py` and its tests
`register()` never validates `depends_on`; only `pipeline()` does, via `graphlib.TopologicalSorter`, raising `MissingDependencyError` (custom, for unregistered deps) or `CycleError` (stdlib, for cycles) with the actual cycle nodes named.

### Explicit `__init__.py` registration trigger
**Source:** RESEARCH.md Pitfall 1
**Apply to:** `tests/core/passes/fakes/__init__.py` (must import every fake-pass module so decorators fire)

### Import-boundary enforcement (CORE-01)
**Source:** RESEARCH.md Code Examples
**Apply to:** `tests/core/test_import_boundaries.py`, run against `src/kir/core/domain/`
AST-based forbidden-import audit — not a `grep`, to catch aliased/dynamic imports. `pydantic` itself is allowed; `pathlib`, `yaml`/`ruamel`, any LLM SDK, `requests`/`httpx`, and markdown-parsing libs are forbidden inside `core/domain/`.

## No Analog Found (in-repo)

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| All 28 files listed above | various | various | Greenfield repository — no `src/`, no `pyproject.toml`, zero prior Python source. Planner must use the RESEARCH.md/ARCHITECTURE.md sketches listed in this document as the authoritative reference instead of in-repo analogs. |

## Metadata

**Analog search scope:** Full repo root (`/Users/mniedre/git/kir`) — confirmed via `ls` and `find` that only `CLAUDE.md`, `LICENSE`, `README.md` exist; no `src/`, no `.py` files, no `pyproject.toml`.
**Files scanned:** 0 (no Python source exists)
**Reference sources substituted:** `.planning/research/ARCHITECTURE.md` (Patterns 1/2/3, Anti-Patterns), `.planning/phases/01-compiler-foundation/01-RESEARCH.md` (Architecture Patterns, Code Examples, Common Pitfalls)
**Pattern extraction date:** 2026-06-30
