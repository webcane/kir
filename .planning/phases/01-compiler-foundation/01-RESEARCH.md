# Phase 1: Compiler Foundation - Research

**Researched:** 2026-06-30
**Domain:** Hexagonal-architecture compiler infrastructure in Python/Pydantic v2 — domain model, ports-as-Protocols, decorator-based pass registry with dependency-driven topological ordering, immutable IR, structured diagnostics, fake-adapter-proven extensibility
**Confidence:** HIGH

## Summary

Phase 1 builds zero new business logic — it builds the *mechanism* that all later phases plug into: domain models, three ports as `typing.Protocol`s, a `PassRegistry` with topological-sort-based dependency ordering, an immutable `CompilerContext`, structured `Diagnostic` value objects, a generic key-value `Cache` Protocol, a minimal `ArtifactManifest`, and a YAML-file-per-artifact `RepositoryPort` implementation. Everything is proven with fakes only — no real Markdown parser, no real LLM call, no real persistent storage beyond a temp-dir-backed fake/real repository used in tests.

This phase's hardest technical problem is not the domain modeling (straightforward Pydantic v2) — it is getting three structural guarantees right at the same time: (1) decorator-based self-registration that still produces deterministic, dependency-correct ordering regardless of import order [VERIFIED via training knowledge — Python's `graphlib.TopologicalSorter`, stdlib since 3.9, documented at docs.python.org]; (2) genuinely immutable IR via Pydantic v2 `frozen=True` + `model_copy(update=...)`, while avoiding a documented gotcha where `model_copy` on a frozen model with a `@cached_property` field silently copies stale cached state [CITED: github.com/pydantic/pydantic/issues/11955]; (3) "byte-identical reruns" as an actual provable test property, which requires controlling non-deterministic Python collection ordering (dict/set iteration in diagnostics or manifest accumulation) independently of Pydantic's already-deterministic field-order serialization [CITED: github.com/pydantic/pydantic/discussions/10343].

**Primary recommendation:** Use Python's standard library `graphlib.TopologicalSorter` for the dependency graph (not a hand-rolled DFS, not a third-party package) — it is stdlib (zero new dependency), raises `CycleError` with the actual cycle nodes on `prepare()`, and its `static_order()` is what `PassRegistry.pipeline()` should call at build time per CONTEXT.md's D-02 decision. Build the domain model and ports exactly as ARCHITECTURE.md's code sketch shows, with two concrete deltas this research surfaces (see "Code Examples" and "Common Pitfalls"): the sketch's `PassRegistry.pipeline()` needs a real topological-sort implementation (currently a comment, `# topological sort over depends_on`), and the sketch's `Pass` Protocol needs a `name`/`depends_on` shape that survives being attached to a plain function via decorator (function attributes, not class attributes) — verify this against `typing.Protocol`'s structural-typing rules during planning, not assume it "just works."

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Domain models (Concept, Relation, Taxonomy, Document, Diagnostic; value objects) | Domain / Core | — | Pure data + invariants; CORE-01 mandates zero I/O or SDK dependency — this is the innermost hexagonal ring by definition |
| Ports (LLMPort, RepositoryPort, MarkdownParserPort) | Domain / Core | — | Interfaces are owned by the domain per dependency-inversion; adapters (not built this phase) will implement them in later phases/packages |
| Pass / PassRegistry / pipeline (topological ordering) | Application (passes ring) | Domain / Core (Pass Protocol type) | Orchestration logic — sequences passes — but the `Pass` Protocol contract itself is a `core/passes/base.py` type, consistent with ARCHITECTURE.md's recommended structure |
| CompilerContext | Application (passes ring) | Domain / Core | Carries ports + run metadata; lives in `core/passes/context.py` per ARCHITECTURE.md, constructed by callers (tests in this phase), never self-constructing |
| Diagnostics accumulation | Domain / Core | Application (passes ring enforces "never halt mid-run") | `Diagnostic` is a domain value object; the *behavior* of always running every pass and accumulating diagnostics (D-01) is a pipeline/application-ring responsibility, not a domain-model responsibility |
| Cache Protocol (generic KV) | Domain / Core (port) | — | Same ownership rule as LLMPort/RepositoryPort — defined in core, no concrete implementation required this phase beyond a fake |
| Artifact Manifest (id + version only) | Domain / Core | Tooling (future: written by repository adapter) | Minimal value object this phase; the *writing* of a manifest file is a tooling-package concern for a later phase, but the manifest's shape (id + version) is defined now as a domain/core type |
| YAML-file-per-artifact repository (fake + real used to prove STOR-01/02) | Tooling (adapter, implements RepositoryPort) | — | Concrete file I/O; per ARCHITECTURE.md this lives in `tooling/repository/`, not `core/` — even though this phase proves it, the adapter code itself does not belong in `core/` |
| Fake LLMPort / fake MarkdownParserPort | Test fixtures (in-repo, not a package) | — | These are not shipped adapters — they exist purely to prove port substitutability per success criterion 4; conventionally live under `tests/fakes/` or `tests/conftest.py`, not under `core/`, `llm/`, or `compiler/` |

## Project Constraints (from CLAUDE.md)

- Compiler architecture over pipelines — discrete, registry-driven passes, not an ad-hoc script chain. **Applies directly**: PassRegistry/pipeline is exactly this mechanism.
- Explicit Pydantic models over dicts — every IR type (Concept, Relation, Taxonomy, Document, Conflict) is a typed, validated contract. **Applies**: no dict-based IR anywhere, including Diagnostic and ArtifactManifest.
- Immutable IR — compiled artifacts are not mutated in place; recompilation produces new artifacts. **Applies directly to CORE-07**: enforce via Pydantic `frozen=True` + `model_copy`.
- Small, independently-testable passes — each pass is unit-testable in isolation, without standing up the full pipeline. **Applies to PASS-03**: fake passes in this phase must each be testable calling `pass_fn(ir, ctx)` directly, no pipeline required.
- No hidden side effects — passes declare their inputs/outputs explicitly; no pass silently depends on another's internal state. **Applies to PASS-04**: enforce via Anti-Pattern 2 avoidance (no pass imports another pass module).
- No global state — configuration and provider selection are threaded explicitly (e.g. via typed `Settings`), never read from ambient globals. **Caveat for this phase**: the `PassRegistry` instance itself is module-level state by design (decorator self-registration requires a module-level registry target) — this is the one sanctioned exception, and the planner should document it as such rather than treat it as a violation. CompilerContext, by contrast, must always be passed explicitly, never read from a global.
- Domain code must have zero LLM SDK / filesystem / YAML imports (`./CLAUDE.md` "Layer Boundaries"). **Applies directly to CORE-01**: this is a structural import-boundary requirement, enforceable as a Phase 1 unit test (`import kir.core...; assert no forbidden imports`), see Code Examples.
- Passes communicate only through the registry/pipeline, never via direct imports of one another (`./CLAUDE.md` "Layer Boundaries"). **Applies directly to PASS-04 and Anti-Pattern 2.**
- No rendering/query/vector-search features. **N/A this phase** — pure infrastructure, no surface area for this violation.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-01 | Domain model has zero import-level dependency on LLM SDKs, filesystem, or YAML libraries | Verified via stdlib-only `import` audit pattern (see Code Examples); enforce as an automated test, not a manual review |
| CORE-02 | System exposes ports (LLMPort, RepositoryPort, MarkdownParserPort) as typed interfaces | `typing.Protocol` (PEP 544), structural typing — no inheritance required of adapters; ARCHITECTURE.md Pattern 2 code sketch is directly usable |
| CORE-03 | Compiler passes register independently (decorator/plugin-based registry) | Decorator self-registration pattern verified against multiple sources; import-order pitfall is the #1 risk — needs an explicit registration-triggering `__init__.py` even though no real passes exist yet (use fakes to prove the mechanism) |
| CORE-04 | Deterministic pipeline; pass dependencies resolved automatically via topological sort | `graphlib.TopologicalSorter` (stdlib, Python 3.9+) is the correct, zero-dependency tool; raises `CycleError` exposing the actual cycle — directly satisfies D-02's "single clear error naming the cycle" requirement |
| CORE-05 | All passes execute inside a shared, immutable CompilerContext | Pydantic `frozen=True` BaseModel (or a plain immutable dataclass — see Open Questions) carrying ports + metadata; constructed once per run by the caller |
| CORE-06 | Every pass returns structured diagnostics (code, severity, location, suggestion) instead of printing/logging | `Diagnostic` as a Pydantic frozen model with a `Severity` enum; per D-01, diagnostics accumulate across all passes and never halt the pipeline mid-run |
| CORE-07 | Passes never mutate IR in place; each pass produces a new immutable artifact | `frozen=True` + `model_copy(update={...})` — verified pattern, with the cached_property gotcha flagged as a pitfall to avoid (don't add `@cached_property` to IR models in this phase) |
| PASS-01 | Every transformation of knowledge is a CompilerPass | Structural requirement satisfied by registry design — no transformation logic exists outside a registered pass, even fake ones |
| PASS-02 | Each pass consumes exactly one IR, produces exactly one IR | Enforced by the `Pass` Protocol's `__call__(ir: IR, ctx: CompilerContext) -> IR` signature — single input, single output, no varargs |
| PASS-03 | Passes are deterministic and independently testable in isolation | Directly provable in this phase: call a fake pass function with a fake IR + fake CompilerContext, assert on output, no pipeline machinery required |
| PASS-04 | Passes communicate only through IR artifacts and CompilerContext | Enforced architecturally (Anti-Pattern 2) — verify via a lint rule or code-review checklist item that no `passes/*.py` file imports another `passes/*.py` file |
| PASS-05 | Pass execution order is derived from declared dependencies, not hardcoded | Same `graphlib.TopologicalSorter` mechanism as CORE-04 — these two requirements share one implementation |
| EXT-01 | New CompilerPass implementations discoverable/registerable without modifying core pipeline | Decorator self-registration + explicit `__init__.py` import list is the standard, fully adequate plugin mechanism here — no need for `importlib.metadata.entry_points()`-based plugin discovery at this project's scale (single-repo, not third-party-plugin-distributed) |
| STOR-01 | Each artifact stored as an individual YAML file, no monolithic JSON | `RepositoryPort` (fake in-memory + a real-but-test-scoped filesystem implementation using `tmp_path`) — one file per fake artifact, proven via test assertion on directory listing |
| STOR-02 | Generated output written to a directory separate from raw sources; raw never modified | Test asserts the repository's write target directory is disjoint from any path treated as "raw source" in the test fixture — trivial to prove with fakes since no real raw source exists yet |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|---------------|
| Python | 3.13+ | Runtime | Per PROJECT.md Constraints — already locked, not re-litigated here. `graphlib` (stdlib since 3.9) and `typing.Protocol` (stdlib since 3.8) are both available with no version risk. [ASSUMED — version carried from STACK.md, not re-verified this session, no change expected] |
| pydantic | 2.13.x (per STACK.md research, 2026-06-29) | Domain model base classes, frozen IR models, Diagnostic, ArtifactManifest | Already verified in prior research session [CITED: STACK.md, sourced from pypi.org/project/pydantic/ same week]. Re-verify the exact pinned version is still current at execution time — do not re-verify here since no new information emerged. |
| graphlib (stdlib) | n/a (stdlib) | `TopologicalSorter` for pass dependency-order resolution | [VERIFIED: docs.python.org/3/library/graphlib.html] — zero new dependency, exact fit for CORE-04/PASS-05. `CycleError` (subclass of `ValueError`) exposes the cycle's node list via `.args[1]`, which is what D-02 requires ("a single clear error naming the cycle"). |
| typing (stdlib) | n/a (stdlib) | `Protocol` for LLMPort/RepositoryPort/MarkdownParserPort/Pass | [VERIFIED: typing.python.org/en/latest/spec/protocol.html, PEP 544] — structural subtyping, no adapter inheritance required. Do not use `@runtime_checkable` + `isinstance()` checks as a substitute for proper testing — `isinstance()` on a Protocol only checks member existence, not signatures, and is documented as potentially slow [CITED: WebSearch cross-referencing typing.python.org and oneuptime.com/blog]. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test runner for all Phase 1 proofs | Already locked in STACK.md. No async tests needed this phase (no real LLM/PydanticAI calls yet — `pytest-asyncio` not needed until Phase 2). |
| ruamel.yaml | 0.19.x | YAML serialization, used by the *real* (not fake) repository implementation this phase proves against `tmp_path` | Already locked in STACK.md for git-diff-friendly, round-trip-faithful YAML. Phase 1 only needs `typ="safe"` mode (no human hand-edit round-trip requirement yet — that's a later-phase concern). |
| pydantic-settings | 2.x | NOT required this phase | Flagged in STACK.md as the standard config-loading tool, but Phase 1 has no CLI/env-var-driven configuration surface — `CompilerContext` is constructed directly by test code and (in later phases) by the composition root. Do not add this dependency in Phase 1 unless a concrete need surfaces. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `graphlib.TopologicalSorter` (stdlib) | Hand-rolled DFS-based topo sort | No reason to hand-roll — stdlib solution is tested, documented, and raises the exact cycle-detection error type D-02 needs. Hand-rolling here would be a "don't hand-roll" violation per this project's own philosophy. |
| `graphlib.TopologicalSorter` (stdlib) | `networkx.topological_sort` | networkx is already a planned dependency (Phase 6, conflict-cycle detection) but pulling it in now for a single-function need (topo sort) when stdlib already solves it is unjustified extra surface area. Reserve networkx for Phase 6's actual cycle-detection-over-semantic-relations use case. |
| Pydantic `frozen=True` BaseModel for CompilerContext | Plain immutable `dataclass(frozen=True)` or `NamedTuple` for CompilerContext specifically | CompilerContext holds Protocol-typed port references (LLMPort, RepositoryPort) plus plain metadata (version strings) — it does not need JSON validation/serialization (it's never persisted), so a frozen dataclass is a legitimate lighter-weight alternative to a Pydantic model here. Pydantic models validate field types strictly at construction, which can be awkward for Protocol-typed fields (Pydantic v2's arbitrary-type support requires `model_config = ConfigDict(arbitrary_types_allowed=True)` for non-Pydantic types like Protocol instances). **Recommendation: use `dataclass(frozen=True, slots=True)` for CompilerContext, reserve Pydantic `BaseModel(frozen=True)` for IR types that ARE persisted/validated** (Document, Concept, Relation, Diagnostic, ArtifactManifest). This is a discretion-area judgment call for the planner — see Open Questions. |
| Decorator self-registration via module-level dict | `importlib.metadata.entry_points()`-based plugin discovery (setuptools/pip-installable plugin packages) | Entry-points discovery is the right tool when third parties ship pass implementations as separate installable packages. KIR's EXT-01 requirement is about not editing the *core pipeline* when adding a pass — it does not require out-of-repo plugin distribution. Decorator + explicit `__init__.py` import list satisfies EXT-01 with far less machinery. Revisit only if KIR ever needs externally-distributed third-party passes. |

**Installation:**
```bash
# No new dependencies beyond what STACK.md already specifies.
# graphlib and typing are stdlib — zero install needed.
uv add "pydantic>=2.13"
uv add --dev "pytest>=8"
```

**Version verification:** No new packages are introduced by this phase beyond what STACK.md (2026-06-29) already verified (pydantic 2.13.x, pytest 8.x). `graphlib` and `typing.Protocol` are Python stdlib — no registry verification applicable. Before scaffolding `pyproject.toml`, re-run `uv add` and confirm the resolved pydantic version still matches or exceeds 2.13.x (training-data and prior-research staleness risk, not a new claim).

## Package Legitimacy Audit

This phase introduces **zero new external packages** beyond what was already verified in `.planning/research/STACK.md` (pydantic, pytest — both already in active use by the time Phase 1 executes, both previously confirmed against PyPI same-week as that research). `graphlib` and `typing.Protocol` used for the registry/ports mechanism are Python standard library — not installable packages, not subject to supply-chain risk.

**slopcheck status this session:** Unable to install slopcheck in this research environment — `pip install slopcheck` was blocked by the sandbox's auto-mode classifier (untrusted-package-install guard), and `pip`/`pip3` were not found on PATH at all in this Python-stdlib-only research pass (no Python project scaffolded yet — greenfield repo). Per the Package Legitimacy Gate's graceful-degradation rule, no packages required gating here because **no new packages are introduced this phase** — pydantic/pytest were already vetted in prior research (STACK.md), and stdlib modules are not subject to registry/supply-chain verification.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|--------------|-----------|--------------|
| pydantic | PyPI | Years (mature) | Very high (>100M/mo class) | github.com/pydantic/pydantic | Not run — pre-verified in STACK.md | Approved (carried over, not re-audited) |
| pytest | PyPI | Years (mature) | Very high | github.com/pytest-dev/pytest | Not run — pre-verified in STACK.md | Approved (carried over, not re-audited) |
| graphlib | stdlib | n/a | n/a | cpython source tree | n/a — stdlib | Approved (no audit applicable) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*If the planner introduces any package beyond pydantic/pytest/stdlib during Phase 1 task-writing (e.g. a test-fixture helper library), it must be run through the full Package Legitimacy Gate before being added to a plan task — this phase's audit covers only what is currently scoped.*

## Architecture Patterns

### System Architecture Diagram

```
                         ┌─────────────────────────────────────────┐
                         │   TEST CODE (this phase's "caller")      │
                         │   constructs fakes, builds CompilerContext│
                         └───────────────────┬───────────────────────┘
                                              │ constructs
                                              ▼
                         ┌─────────────────────────────────────────┐
                         │         CompilerContext (frozen)          │
                         │  ports: llm, repository, parser           │
                         │  metadata: compiler_version, schema_version│
                         └───────────────────┬───────────────────────┘
                                              │ passed to every pass call
                                              ▼
   register_pass()        ┌─────────────────────────────────────────┐
   (decorator, import-time)│           PassRegistry                  │
   ────────────────────►  │  ._passes: dict[str, Pass]                │
   fake_pass_a             │  .pipeline() -> graphlib.TopologicalSorter│
   fake_pass_b              │              .static_order()             │
   fake_pass_c (depends on  │  raises CycleError / missing-dep error   │
    a, b)                   │  at BUILD time (not registration time)   │
                            └───────────────────┬───────────────────────┘
                                              │ ordered list of passes
                                              ▼
                         ┌─────────────────────────────────────────┐
                         │     Pipeline Executor (test harness loop) │
                         │  for pass in pipeline():                  │
                         │      ir, new_diagnostics = pass(ir, ctx)   │
                         │      diagnostics += new_diagnostics        │  ← never halts on Error (D-01)
                         │      # ir is a NEW frozen instance each time│
                         └───────────────────┬───────────────────────┘
                                              │ final IR + accumulated Diagnostics
                                              ▼
                         ┌─────────────────────────────────────────┐
                         │      RepositoryPort.save(artifact)        │
                         │  (fake: in-memory dict)                   │
                         │  (real, test-scoped: one YAML file per    │
                         │   artifact, written under tmp_path/kir/,  │
                         │   never under tmp_path/raw/)               │
                         └─────────────────────────────────────────┘

   Ports (Protocols, defined in core, never imported by adapters' SDKs):
   ┌───────────┐  ┌────────────────┐  ┌──────────────────┐
   │ LLMPort   │  │ RepositoryPort │  │ MarkdownParserPort│
   └───────────┘  └────────────────┘  └──────────────────┘
        ▲                  ▲                    ▲
        │ satisfied by     │ satisfied by        │ satisfied by
   FakeLLMPort      FakeRepository /      FakeMarkdownParser
   (test double)     RealYamlRepository    (test double)
                      (test-scoped real)
```

A reader can trace the primary use case (prove a fake pass registers, orders correctly, and produces an immutable artifact diagnostics-and-all) entirely through this diagram: test code constructs `CompilerContext` with fakes → decorator-registered fake passes are pulled from `PassRegistry.pipeline()` in dependency order → executor loop calls each pass, accumulating diagnostics and replacing `ir` with each pass's return value → final artifact is saved via `RepositoryPort`, producing one file per artifact in a directory disjoint from any raw-source path.

### Recommended Project Structure

This phase only needs to stand up the `core` package per ARCHITECTURE.md's 5-package split — the other four packages (`compiler/documents`, `compiler/knowledge`, `llm`, `tooling`) are not populated with real adapters this phase, but `tooling/repository/` does need a thin **test-scoped** YAML repository implementation to prove STOR-01/STOR-02 (success criterion 5 explicitly requires "writing a fake artifact through the repository port"). Per CONTEXT.md's "Claude's Discretion," this follows ARCHITECTURE.md's structure unless a concrete conflict surfaces — none did.

```
src/kir/
├── core/
│   ├── domain/
│   │   ├── models/
│   │   │   ├── document.py            # Document IR (Document, Section) — entity
│   │   │   ├── concept.py             # Concept entity
│   │   │   ├── relation.py            # Relation value object
│   │   │   ├── taxonomy.py            # Taxonomy value object
│   │   │   ├── conflict.py            # Conflict value object (not exercised this phase, but per CORE-01's full entity list — see Open Questions on scope)
│   │   │   ├── provenance.py          # Provenance value object (SourceRef)
│   │   │   └── diagnostic.py          # Diagnostic value object (code, severity, location, suggestion) — CORE-06
│   │   ├── value_objects.py           # ConceptId, RelationId, Checksum, SourceRef — or split per-file, planner's call
│   │   ├── manifest.py                # ArtifactManifest (id + version only, per D-04)
│   │   └── ir.py                      # DocumentIR / KnowledgeIR aggregate envelopes (or thin fake IR types for this phase's proofs — see Open Questions)
│   ├── ports/
│   │   ├── llm_port.py                # LLMPort Protocol
│   │   ├── repository_port.py         # RepositoryPort Protocol
│   │   ├── parser_port.py             # MarkdownParserPort Protocol
│   │   └── cache_port.py              # Cache Protocol (generic KV — get/set, per D-03)
│   ├── passes/
│   │   ├── base.py                    # Pass Protocol: __call__(ir, ctx) -> ir
│   │   ├── registry.py                # PassRegistry: register(), pipeline() [graphlib.TopologicalSorter]
│   │   └── context.py                 # CompilerContext (ports + run metadata)
│   └── config/
│       └── versions.py                # compiler_version, schema_version, prompt_version constants
│
└── tooling/
    └── repository/
        └── yaml_repository.py         # Implements RepositoryPort — one YAML file per artifact
                                        # (test-scoped this phase: proven via tmp_path, not wired to a CLI yet)

tests/
├── core/
│   ├── domain/
│   │   └── test_*.py                  # Per-model construction/invariant/immutability tests
│   ├── passes/
│   │   ├── test_registry.py           # Registration, topo-order, cycle/missing-dep errors at build time
│   │   ├── test_pipeline_execution.py # Byte-identical rerun proof, diagnostics accumulation proof
│   │   └── fakes/
│   │       ├── fake_passes.py         # Trivial fake CompilerPass implementations exercising dependency graphs
│   │       ├── fake_llm_port.py       # FakeLLMPort satisfying LLMPort
│   │       ├── fake_repository.py     # In-memory FakeRepository satisfying RepositoryPort
│   │       └── fake_parser.py         # FakeMarkdownParser satisfying MarkdownParserPort
│   └── test_import_boundaries.py      # CORE-01: asserts core.domain has zero forbidden imports
└── tooling/
    └── repository/
        └── test_yaml_repository.py    # STOR-01/STOR-02 proof against tmp_path
```

### Pattern 1: Decorator-Based Self-Registration with Build-Time Topological Sort

**What:** Each fake pass is a plain function decorated with `@register_pass(name=..., depends_on=(...))`. The decorator attaches `name`/`depends_on` as function attributes and inserts the function into a module-level `PassRegistry`. `PassRegistry.pipeline()` is called once, lazily, at the point the test harness needs an ordered pass list — never at `register_pass()` time. This is what makes CONTEXT.md's D-02 decision implementable.

**When to use:** Every CompilerPass in the project (this phase: fake passes only).

**Example:**
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

**Gap surfaced vs. ARCHITECTURE.md's sketch:** the canonical sketch's `pipeline()` body is literally a comment (`# topological sort over depends_on`) — it was never implemented in research, only described. This is the single largest concrete gap the planner must close: write the real `graphlib`-based implementation (above), not assume the sketch is executable as-is.

### Pattern 2: Frozen Pydantic Models with `model_copy` for CORE-07 Immutability

**What:** Every IR-bearing model (`Document`, `Concept`, `Relation`, `Diagnostic`, fake test IRs) is declared with `model_config = ConfigDict(frozen=True)`. Passes never call `ir.field = x`; they always return `ir.model_copy(update={...})`.

**When to use:** All domain/IR models, this phase and every phase after.

**Example:**
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

```python
# A trivial fake IR used only to prove pass mechanics (not a real Document/Concept type)
class FakeIR(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: int = 0
    diagnostics: tuple[Diagnostic, ...] = ()   # tuple, not list — list is mutable and breaks hashability/frozen guarantees
```

**Pitfall avoided:** Do not put `@cached_property` on any frozen IR model field in this phase — `model_copy()` on a frozen model with a `@cached_property` silently copies the *cached* value into the new instance, which can desync from the new field values [CITED: github.com/pydantic/pydantic/issues/11955]. If memoized derived values are ever needed later, compute them as plain methods, not cached properties, until/unless this Pydantic behavior changes.

**Pitfall avoided:** Use `tuple[...]` (or another hashable/immutable container), not `list[...]`, for any "accumulating" field like `diagnostics` on a frozen model — a `list` field on a frozen Pydantic model is still internally mutable via `.append()` even though direct field reassignment (`ir.diagnostics = x`) raises; only reassignment is blocked by `frozen=True`, not in-place mutation of a mutable field's contents. This is a real, easy-to-miss CORE-07 violation vector and should be an explicit code-review checklist item.

### Pattern 3: Ports as Protocols, Verified by Multiple Interchangeable Fakes (not just one)

**What:** Each port (`LLMPort`, `RepositoryPort`, `MarkdownParserPort`) is a `typing.Protocol`. Success criterion 4 requires proving each fake "can be swapped in CompilerContext without any domain or pass code change" — the strongest proof of this is writing **two** fake implementations of at least one port (e.g. two different `FakeRepository` variants: pure in-memory dict, and tmp_path-backed YAML) and running the *same* test logic against both via a shared pytest fixture/parametrize, not just asserting "a fake exists."

**When to use:** This phase's port-substitutability proofs.

**Example:**
```python
# core/ports/repository_port.py
from typing import Protocol

class RepositoryPort(Protocol):
    def save(self, artifact_id: str, artifact: object) -> None: ...
    def load(self, artifact_id: str) -> object: ...
```

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

This single parametrized contract test is what actually proves "swappable without domain/pass code change" — a single hand-written fake with no contract test only proves "a fake exists," not "the port boundary is real."

### Anti-Patterns to Avoid

- **Validating `depends_on` at `register_pass()` call time:** Explicitly forbidden by D-02. Registration must always succeed; only `pipeline()` validates the full graph.
- **A pass importing another pass module directly:** Anti-Pattern 2 from ARCHITECTURE.md. Even fake passes in this phase must respect this — a fake pass "looking up" another fake pass's output via direct import, rather than via the IR field the pipeline already threaded through, defeats the entire point of proving the registry mechanism.
- **`isinstance()`-based Protocol runtime checks as the primary test strategy:** `@runtime_checkable` + `isinstance()` only checks attribute/method *existence*, not signatures — a fake with a same-named method but wrong return type would pass an `isinstance()` check and still fail real usage. Prefer calling the fake through actual pass/registry code (functional tests) over `isinstance()` assertions.
- **Using `list` fields for "accumulating" state on frozen models:** see Pattern 2 pitfall above — use `tuple`.
- **CompilerContext as a Pydantic `BaseModel` without `arbitrary_types_allowed`:** Protocol-typed fields (`llm: LLMPort`) are not native Pydantic types; either set `model_config = ConfigDict(arbitrary_types_allowed=True)` explicitly, or (recommended, see Standard Stack) use a frozen `dataclass` instead, since CompilerContext is never serialized/validated from external data.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| Pass dependency ordering / cycle detection | Custom DFS-based topological sort | `graphlib.TopologicalSorter` (stdlib) | Already implemented, tested, documented; raises `CycleError` with the actual cycle nodes — exactly what D-02 needs. Hand-rolling this duplicates a stdlib module for no benefit and risks subtle ordering bugs (e.g. non-deterministic iteration over `dict`/`set` without explicit sort, which would itself threaten the "byte-identical reruns" success criterion). |
| Immutable model updates | Custom `__setattr__` override or manual `copy.deepcopy` + field patching | Pydantic v2 `frozen=True` + `model_copy(update=...)` | Native, validated, and already the project's chosen IR framework — no reason to reimplement immutability semantics Pydantic already provides correctly. |
| Structural interface checking | Custom "duck typing" helper or `hasattr()` chains | `typing.Protocol` | PEP 544-standardized, IDE/type-checker (pyright/mypy) supported, zero runtime cost unless `@runtime_checkable` is explicitly opted into. |
| YAML serialization with stable key order | Hand-rolled dict-to-YAML-string formatter | `ruamel.yaml` (already locked in STACK.md) | Already researched and selected specifically to avoid PyYAML's key-reordering/comment-dropping problems; re-confirmed here as still correct for the test-scoped repository this phase needs. |

**Key insight:** This phase is unusually hand-roll-resistant by design — every hard problem it needs to solve (topological sort, immutable updates, structural interfaces) already has a correct, standard, zero-or-near-zero-dependency solution. The risk in Phase 1 is not "no library exists," it's "the team reaches for a hand-rolled version out of habit before checking stdlib/Pydantic already solves it" — flag any task that proposes writing a custom topo-sort or custom immutability mechanism for review.

## Common Pitfalls

### Pitfall 1: Decorator Registration Never Fires Because the Module Was Never Imported
**What goes wrong:** A fake pass is defined and decorated, but the test (or pipeline) that expects it to be registered fails because the module containing the decorator was never imported anywhere in the test run's import graph.
**Why it happens:** Decorators only execute their side effect (registration) when the containing module is imported — Python does not eagerly scan the filesystem for decorated functions [CITED: multiple WebSearch sources cross-referencing Real Python and dontusethiscode.com, consistent with well-known Python semantics].
**How to avoid:** Use an explicit `__init__.py` (or a dedicated test fixture module) that imports every fake-pass module, mirroring ARCHITECTURE.md's stated mitigation ("an explicit `passes/document/__init__.py` and `passes/knowledge/__init__.py` that import every pass module so registration always fires"). For this phase, the equivalent is a `tests/core/passes/fakes/__init__.py` that imports all fake pass modules.
**Warning signs:** `PassRegistry.pipeline()` returns fewer passes than expected, or `KeyError`/`MissingDependencyError` appears for a pass that "should" be registered — first check whether its module was actually imported by the running test.

### Pitfall 2: "Byte-Identical Reruns" Fails Due to Non-Deterministic Collection Iteration, Not Pydantic Serialization
**What goes wrong:** A test asserts two compile runs produce byte-identical YAML/JSON output, but the assertion intermittently fails (or worse, passes locally and fails in CI) because diagnostics or manifest entries were accumulated into a `set` or built from `dict.values()` iteration without an explicit sort.
**Why it happens:** Pydantic v2's `model_dump`/`model_dump_json` is itself deterministic (field-declaration order) [CITED: github.com/pydantic/pydantic/discussions/10343] — the non-determinism, if any, comes from *upstream* Python code building the data that gets serialized, not from Pydantic's serializer itself. `PassRegistry._passes` being a plain `dict` is fine in CPython 3.7+ (insertion-ordered), but any place the code does `set(...)` over pass names, or iterates a `dict` built from multiple unordered sources (e.g. merging two registries), is a determinism risk.
**How to avoid:** Write the success-criterion-3 "byte-identical reruns" test as an actual round-trip test (run the same fake pipeline twice against the same fake inputs, serialize both outputs, assert byte equality) early — not as an afterthought. If it ever flakes, the fix is almost always "sort this collection explicitly by a stable key" rather than "something is wrong with Pydantic."
**Warning signs:** A determinism test passes most of the time but fails occasionally, especially under `pytest-xdist` parallel test ordering or across separate CI runs — that pattern points directly at unsorted iteration, not Pydantic.

### Pitfall 3: `model_copy(update=...)` Silently Bypasses Validators
**What goes wrong:** A pass uses `ir.model_copy(update={"some_field": bad_value})` and the resulting frozen model is constructed with an invalid value that a normal `Model(...)` construction or `.model_validate()` call would have rejected.
**Why it happens:** `model_copy()` is explicitly a *shallow copy with field replacement* operation, not a full re-validation — Pydantic v2's documented behavior is that `model_copy` does not re-run validators on the updated fields by design (performance trade-off).
**How to avoid:** For this phase's fake passes, this risk is low (trivial fake IRs, no complex invariants), but the planner should flag this as a Phase 2+ concern when real IR types (Document, Concept) gain invariants like slug-derived IDs — at that point, consider whether passes should validate critical invariants explicitly after `model_copy`, or whether `model_validate(model_copy(...).model_dump())` round-tripping is needed for fields with strict invariants. Not a blocking issue for Phase 1's fakes, but worth a code comment/TODO so it isn't silently inherited as an assumption into Phase 2.
**Warning signs:** A test that should catch an invalid field value via a Pydantic validator doesn't — usually traced back to a `model_copy(update=...)` call that introduced the bad value.

### Pitfall 4: Conflating "Domain has zero LLM/filesystem/YAML imports" with "Domain has zero imports from outside `core/`"
**What goes wrong:** A planner/implementer interprets CORE-01 too broadly (forbidding any non-stdlib import in `core/domain/`) or too narrowly (only checking for `import openai`/`import yaml` literally, missing transitive imports via a helper module).
**Why it happens:** CORE-01's text is specific (LLM SDKs, filesystem, YAML libraries) but the spirit (per CLAUDE.md's "Layer Boundaries") is broader: domain code must not depend on *any* adapter-side concern, including `pathlib`-based file logic (explicitly called out in ARCHITECTURE.md's Anti-Pattern 1 example, `Concept.from_yaml()`).
**How to avoid:** Write the CORE-01 verification test as an actual import-graph audit (e.g. parse `core/domain/**/*.py` with `ast`, collect all `import`/`from X import Y` statements, assert none of them are in a forbidden list: `{"yaml", "ruamel", "openai", "anthropic", "pydantic_ai", "pathlib", "os", "requests", "httpx"}` — note `pydantic` itself is explicitly allowed). A simple `grep`-based check is a reasonable first pass but an AST-based test is more robust against import aliasing (`import yaml as y`) or `importlib.import_module("yaml")` dynamic imports.
**Warning signs:** A domain model gains a "convenience" method that quietly does file I/O or string formatting that assumes a specific serialization format — this is exactly Anti-Pattern 1 and should be caught by code review even before the automated test would catch it.

## Code Examples

### CORE-01 Import Boundary Verification Test
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
Source: pattern synthesized from this project's own CLAUDE.md "Layer Boundaries" requirement; `ast`-based static analysis is stdlib, no external dependency.

### Byte-Identical Rerun Proof (Success Criterion 3)
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

### D-02 Build-Time Error Detection Proof
```python
# tests/core/passes/test_registry.py
from graphlib import CycleError
from core.passes.registry import PassRegistry, MissingDependencyError

def test_missing_dependency_detected_at_pipeline_build_time():
    registry = PassRegistry()
    registry.register(_fake_pass("a", depends_on=("nonexistent",)))
    # Registration itself must NOT raise (D-02):
    # (the .register() call above already succeeded if we got here)
    with pytest.raises(MissingDependencyError, match="nonexistent"):
        registry.pipeline()

def test_circular_dependency_detected_at_pipeline_build_time():
    registry = PassRegistry()
    registry.register(_fake_pass("a", depends_on=("b",)))
    registry.register(_fake_pass("b", depends_on=("a",)))
    with pytest.raises(CycleError):
        registry.pipeline()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---------------|-------------------|---------------|--------|
| Hand-rolled DFS topo sort, or third-party `toposort` package | `graphlib.TopologicalSorter` (stdlib) | Available since Python 3.9 (2020) — not a recent change, but still commonly hand-rolled out of habit/unfamiliarity | Zero new dependency, well-tested cycle detection with actual cycle node reporting |
| Pydantic v1 `.copy(update=...)`, `class Config:` | Pydantic v2 `.model_copy(update=...)`, `model_config = ConfigDict(...)` | Pydantic v2 release (2023), already accounted for in STACK.md | Already correctly reflected in this project's existing research — flagged here only as a reminder for Phase 1 implementers not to copy v1-flavored snippets from older tutorials |

**Deprecated/outdated:** None newly discovered this session beyond what STACK.md already flagged (Pydantic v1 patterns, PyYAML as primary serializer).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | CompilerContext should be a frozen `dataclass`, not a Pydantic `BaseModel`, because it holds Protocol-typed port fields and is never serialized | Standard Stack / Alternatives Considered, Open Questions | Low-medium: if the planner instead uses a Pydantic model with `arbitrary_types_allowed=True`, both approaches work — this is a design-taste recommendation, not a correctness-blocking claim. Flagging as assumed because ARCHITECTURE.md's sketch uses a plain `__init__`-based class (neither dataclass nor Pydantic), so this phase's planner must make an explicit choice not fully dictated by prior research. |
| A2 | `Pass` Protocol's `name`/`depends_on` should be implemented as function attributes (not a class-based Pass implementation) to keep the decorator pattern lightweight | Architecture Patterns, Pattern 1 | Low: this matches ARCHITECTURE.md's existing code sketch exactly (`fn.name = name; fn.depends_on = depends_on`) — flagged as assumed only because Protocol structural-typing compatibility with function-attribute-attachment (rather than class instance attributes) should be spot-checked with a real `Protocol` + `isinstance`/type-checker pass during planning, not assumed to "just work" without verification. |
| A3 | The "Conflict" domain model belongs in Phase 1's `core/domain/models/` even though no pass in Phase 1 produces/consumes Conflict objects | Recommended Project Structure | Low: CORE-01's text explicitly lists "Concept, Relation, Taxonomy, Document entities" but ARCHITECTURE.md's structure also includes `conflict.py` at the same tier. If the planner decides Conflict belongs to a later phase instead (it's not exercised until Phase 6 per ROADMAP.md), descoping it from Phase 1 is a reasonable, low-risk alternative — flagged because REQUIREMENTS.md's CORE-01 text doesn't explicitly name Conflict the way the phase's own Success Criterion 1 does ("Concept, Relation, Taxonomy, Document entities; ConceptId, RelationId, Checksum, SourceRef value objects" — no Conflict, no Diagnostic named in the *entity* list, though Diagnostic is separately required by CORE-06). The planner should resolve this scope question explicitly rather than silently include or exclude Conflict. |
| A4 | No new third-party Python package is needed for "fake" test doubles beyond what's in STACK.md (no mocking library like `unittest.mock`-alternatives needed) | Standard Stack | Low: hand-written fake classes (not `Mock()`/`MagicMock()`) are the correct choice here per the "verified fakes" testing philosophy this research surfaced — using `unittest.mock.Mock()` instead of real fake classes would weaken the Protocol-substitutability proof (a `Mock()` satisfies almost any `isinstance` check trivially, which is the opposite of what success criterion 4 needs to demonstrate). |

**If this table is empty:** N/A — see entries above. All four are low-risk design-judgment items, not contested factual claims; none require live user confirmation before planning proceeds, but the planner should make each choice explicit in PLAN.md rather than leaving it implicit.

## Open Questions

1. **Should `CompilerContext` be a Pydantic `BaseModel(frozen=True)` or a `dataclass(frozen=True, slots=True)`?**
   - What we know: ARCHITECTURE.md's sketch uses a plain class with `__init__`; CONTEXT.md doesn't specify; CompilerContext holds Protocol-typed ports (not natively Pydantic-validatable without `arbitrary_types_allowed=True`) plus plain version strings.
   - What's unclear: whether the project wants CompilerContext to be a Pydantic model for consistency with "every IR type is Pydantic" (CLAUDE.md's "Explicit Pydantic models over dicts" principle) even though CompilerContext isn't really an IR type (it's not persisted, not part of the Knowledge IR).
   - Recommendation: Use a frozen `dataclass` — it's not an IR artifact, it's a dependency-injection container, and forcing Pydantic validation onto Protocol-typed fields adds friction without benefit. The planner should make this explicit in PLAN.md so it isn't silently inconsistent across tasks.

2. **Does Phase 1 need a real (filesystem-backed) `YamlFileRepository`, or is an in-memory fake sufficient to satisfy STOR-01/STOR-02?**
   - What we know: Success criterion 5 says "Writing a fake artifact through the repository port produces one individual YAML file per artifact... in a directory that is verifiably separate from any raw-source directory" — this language ("YAML file," "directory") strongly implies real filesystem I/O is required, not just an in-memory dict pretending to be files.
   - What's unclear: whether this real-filesystem repository implementation belongs to `tooling/repository/` permanently (i.e., this is actually the first real piece of the eventual production repository adapter, just proven early) or whether it's explicitly throwaway test scaffolding to be rebuilt properly in a later phase.
   - Recommendation: Build it as the real, permanent `tooling/repository/yaml_repository.py` (per Pattern 3 above) — there's no reason to throw away working repository-adapter code, and STOR-01/02 read as wanting proof against actual file I/O, not a simulation of it. The planner should treat this as the first concrete adapter code in the project, even though "no real pass, parser, or LLM adapter is written in this phase" (per CONTEXT.md) — the repository adapter is explicitly exempted by STOR-01/02's literal "produces... a YAML file" language.

3. **What is the minimal "fake IR" type set needed to prove PASS-01 through PASS-05 and CORE-04/05/06/07 without building real Document/Concept/Relation IR types yet?**
   - What we know: CONTEXT.md's "Claude's Discretion" explicitly leaves "exact shape of the fake passes/adapters... how many, what dependency graphs they exercise" to planning.
   - What's unclear: whether the same `Concept`/`Relation`/`Taxonomy`/`Document` domain models required by CORE-01's entity list should *also* serve as the "fake IR" used in pass-mechanics tests, or whether a wholly separate, simpler `FakeIR` type (as sketched in this research's Code Examples) should be used to keep pass-mechanics tests decoupled from domain-model schema changes in later phases.
   - Recommendation: Build the real domain models (Concept, Relation, Taxonomy, Document, Diagnostic, value objects) to satisfy CORE-01 directly (their own dedicated construction/invariant tests), but use a separate minimal `FakeIR` Pydantic model (as in this research's examples) for the pass-registry/pipeline mechanics tests — this keeps "does the registry topo-sort correctly" tests independent of "does Document have the right fields" tests, so a later schema change to Document doesn't ripple into registry tests. This is a discretion-area judgment call the planner should make explicit, not an open question requiring user input.

## Environment Availability

This phase has no external service dependencies (no database, no LLM API, no network calls) — it is pure Python code + pytest + filesystem (via `tmp_path`, pytest's built-in temp-directory fixture, not a real persistent directory).

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.13+ | All code | Not verified this session — no `python3`/`pip` found on PATH in this research sandbox | — | Verify at execution time via `uv python pin 3.13` per STACK.md's installation instructions; this is a project-scaffolding step, not a research blocker (greenfield repo, `pyproject.toml` doesn't exist yet) |
| uv | Dependency management | Not verified this session | — | Must be installed before Phase 1 execution begins; flag as a Wave 0 / setup-task dependency for the planner, not a Phase 1 code task |
| graphlib, typing (stdlib) | Pass registry, ports | Implicitly available with any Python 3.9+/3.8+ install | stdlib | None needed |

**Missing dependencies with no fallback:**
- None — this research environment lacking `python3`/`pip`/`uv` on PATH does not block Phase 1 planning (it's a documentation/research task, not code execution), but the planner should add an explicit "verify `uv`/Python 3.13 toolchain is installed" check as the very first task of Phase 1's plan, since this is a genuinely greenfield repository (no `pyproject.toml` exists yet per the `code_context` in CONTEXT.md).

**Missing dependencies with fallback:**
- None applicable.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (per STACK.md; not yet installed — greenfield repo) |
| Config file | none yet — Wave 0 must create `pyproject.toml` with `[tool.pytest.ini_options]` and a `tests/` root |
| Quick run command | `uv run pytest tests/core -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|---------------|
| CORE-01 | Domain has zero LLM/filesystem/YAML imports | unit (static analysis) | `pytest tests/core/test_import_boundaries.py -x` | Wave 0 |
| CORE-02 | Ports are typed Protocols satisfied structurally by adapters | unit | `pytest tests/core/ports/ -x` | Wave 0 |
| CORE-03 | Passes self-register via decorator without editing existing files | unit | `pytest tests/core/passes/test_registry.py::test_new_pass_registers_without_editing_existing -x` | Wave 0 |
| CORE-04 | Pipeline executes passes in dependency-declared order | unit | `pytest tests/core/passes/test_registry.py::test_pipeline_orders_by_dependency -x` | Wave 0 |
| CORE-05 | All passes execute inside shared immutable CompilerContext | unit | `pytest tests/core/passes/test_context.py -x` | Wave 0 |
| CORE-06 | Every pass returns structured Diagnostics, never prints/logs | unit | `pytest tests/core/passes/test_pipeline_execution.py::test_diagnostics_are_structured -x` | Wave 0 |
| CORE-07 | Passes never mutate IR in place; produce new immutable artifact | unit | `pytest tests/core/domain/test_immutability.py -x` | Wave 0 |
| PASS-01..05 | Pass contract (one-in-one-out, isolated, registry-ordered, no side-channel comms) | unit | `pytest tests/core/passes/ -x` | Wave 0 |
| EXT-01 | New pass addable without modifying core pipeline file | unit | `pytest tests/core/passes/test_registry.py::test_new_pass_registers_without_editing_existing -x` | Wave 0 |
| STOR-01 | One YAML file per artifact, no monolithic JSON | unit (filesystem, `tmp_path`) | `pytest tests/tooling/repository/test_yaml_repository.py::test_one_file_per_artifact -x` | Wave 0 |
| STOR-02 | Output directory separate from raw source directory | unit (filesystem, `tmp_path`) | `pytest tests/tooling/repository/test_yaml_repository.py::test_output_dir_disjoint_from_raw -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/core -x -q` (fast subset, this phase's primary scope)
- **Per wave merge:** `uv run pytest -x -q` (full suite — small at this phase, cheap to run in full every time)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `pyproject.toml` with `[tool.pytest.ini_options]`, `src/` layout declared, pydantic/pytest dependencies — project does not exist yet (confirmed greenfield per CONTEXT.md `code_context`)
- [ ] `tests/conftest.py` — shared fixtures: `fake_compiler_context`, `fake_registry`, `tmp_path`-based repository fixture
- [ ] `tests/core/passes/fakes/__init__.py` — explicit import list to trigger fake-pass decorator registration (Pitfall 1 mitigation)
- [ ] Framework install: `uv add --dev pytest` (and `uv add pydantic`) — no test framework currently installed anywhere in the repo

*(All gaps listed — this is a from-scratch project, so the entire test infrastructure is a Wave 0 deliverable, not a partial gap.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|---------------------|
| V2 Authentication | No | Phase 1 has no auth surface — pure library code, no network/user-facing entrypoint |
| V3 Session Management | No | No sessions exist in a compiler library |
| V4 Access Control | No | No multi-user/access-control surface this phase |
| V5 Input Validation | Yes | Pydantic v2 `BaseModel` validation (strict types, no `extra="allow"` on domain models) is the standard control — every IR/Diagnostic/Manifest field is validated at construction via Pydantic, not hand-parsed |
| V6 Cryptography | No | No cryptographic operations in Phase 1 (Checksum value object exists as a type but its hashing algorithm/implementation is not exercised by any real pass yet — flag for Phase 2/5 research when checksums are actually computed from real document content) |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|------------------------|
| Permissive Pydantic config silently accepting malformed/unexpected fields on a domain model (`extra="ignore"` or default `extra="allow"`-equivalent laxity) | Tampering (silent data corruration) | Use `model_config = ConfigDict(extra="forbid")` on every domain/IR model — this is explicitly the pitfall PITFALLS.md flagged project-wide ("Structured-output validation silently coerced") and is just as applicable to Phase 1's own Diagnostic/ArtifactManifest models as it will be to Phase 2's LLM-output models. Set this convention now so it's inherited by every later model, not retrofitted. |
| Path traversal via unvalidated `artifact_id` used directly as a filename in the repository adapter (e.g. `artifact_id = "../../etc/passwd"`) | Tampering / Information Disclosure | Even though Phase 1's repository is test-scoped (`tmp_path`), if `YamlFileRepository` becomes the permanent adapter (see Open Question 2), the planner should ensure `artifact_id` is validated/sanitized (e.g. derived from a slug or UUID, never raw user/LLM-controlled text) before being used to construct a filesystem path — `pathlib.Path` doesn't auto-prevent `..` traversal. Low real-world risk this phase (all artifact IDs are test-constructed), but worth a code-review note since this adapter is likely to persist into later phases unchanged. |
| Decorator self-registration accepting an unbounded/untrusted `depends_on` tuple that could reference passes from a different, unrelated registry (cross-registry confusion) | Tampering | Not a realistic threat in this single-process, single-author-codebase context (no untrusted plugin loading happens in v1 per EXT-01's resolved scope) — noted only because ASVS V5 input validation principles apply structurally even to internal APIs: `PassRegistry.register()` should reject non-`Pass`-shaped objects early (fail fast) rather than allow a malformed pass object to propagate into `pipeline()` and produce a confusing downstream error. |

## Sources

### Primary (HIGH confidence)
- [graphlib — Functionality to operate with graph-like structures (Python official docs)](https://docs.python.org/3/library/graphlib.html) — `TopologicalSorter`, `CycleError` semantics
- [Protocols — typing documentation (official)](https://typing.python.org/en/latest/spec/protocol.html) — structural subtyping spec
- [PEP 544 – Protocols: Structural subtyping](https://peps.python.org/pep-0544/) — official protocol spec
- `.planning/research/ARCHITECTURE.md` — canonical project architecture research (already-approved, this phase builds directly on its Recommended Project Structure / Architectural Patterns / Anti-Patterns)
- `.planning/research/STACK.md` — canonical stack research (pydantic, pytest, ruamel.yaml versions and rationale)
- `.planning/research/SUMMARY.md` — canonical synthesis (build order, pitfalls)
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/phases/01-compiler-foundation/01-CONTEXT.md` — phase scope, locked decisions, requirement text

### Secondary (MEDIUM confidence)
- [Replacing values for frozen models — Pydantic GitHub Discussion #3352](https://github.com/pydantic/pydantic/discussions/3352) — `model_copy(update=...)` pattern confirmation
- [Is model_dump_json deterministic? — Pydantic GitHub Discussion #10343](https://github.com/pydantic/pydantic/discussions/10343) — field-order determinism confirmation
- [model_copy with frozen=True copies cached_property cache — Pydantic Issue #11955](https://github.com/pydantic/pydantic/issues/11955) — cached_property + frozen + model_copy gotcha
- [Fast tests for slow services: why you should use verified fakes — pythonspeed.com](https://pythonspeed.com/articles/verified-fakes/) — contract-test-against-multiple-fakes pattern
- WebSearch cross-referencing Real Python, dontusethiscode.com, blog.miguelgrinberg.com — decorator self-registration import-order pitfall (consistent across independent sources)

### Tertiary (LOW confidence)
- None used as load-bearing claims this session — all findings above were corroborated by at least one official/primary source.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages introduced; stdlib `graphlib`/`typing.Protocol` verified against official docs; pydantic/pytest carried over from already-HIGH-confidence STACK.md
- Architecture: HIGH — builds directly on already-approved ARCHITECTURE.md; the one concrete gap found (unimplemented `pipeline()` body in the canonical sketch) is now closed with a verified stdlib-based implementation
- Pitfalls: HIGH — all four pitfalls trace to either official Pydantic GitHub issues/discussions or well-corroborated, independently-sourced Python community knowledge about decorator/import-order semantics

**Research date:** 2026-06-30
**Valid until:** ~60 days (stdlib modules and PEP 544 are stable, non-fast-moving; re-verify pydantic version pin only if Phase 1 execution is delayed significantly past the STACK.md research date)
