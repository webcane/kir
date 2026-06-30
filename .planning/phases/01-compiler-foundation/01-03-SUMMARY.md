---
phase: 01-compiler-foundation
plan: 03
subsystem: core
tags: [graphlib, dataclass, protocol, pass-registry, dependency-injection, tdd]

# Dependency graph
requires: ["01-01", "01-02"]
provides:
  - "Pass Protocol (src/kir/core/passes/base.py): name, depends_on, __call__(ir, ctx) -> ir"
  - "PassRegistry (src/kir/core/passes/registry.py): register() never validates depends_on (D-02), pipeline() builds dependency-ordered list via graphlib.TopologicalSorter, raising MissingDependencyError or CycleError at build time"
  - "CompilerContext (src/kir/core/passes/context.py): frozen, slotted dataclass DI container carrying llm/repository/parser ports + compiler_version/schema_version, always explicitly constructed, never global"
  - "compiler_version, schema_version, prompt_version constants (src/kir/core/config/versions.py)"
affects: ["01-04", "phase-02"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "graphlib.TopologicalSorter (stdlib) for pass dependency ordering and cycle detection — no hand-rolled DFS"
    - "Build-time-only dependency validation (D-02): register() always succeeds; pipeline() is the sole validation point"
    - "CompilerContext as frozen(slots=True) dataclass, not Pydantic BaseModel — Protocol-typed port fields, never serialized"
    - "TYPE_CHECKING-guarded forward reference (base.py -> context.py) to avoid circular import"

key-files:
  created:
    - src/kir/core/passes/base.py
    - src/kir/core/passes/context.py
    - src/kir/core/passes/registry.py
    - src/kir/core/config/versions.py
    - tests/core/passes/test_base.py
    - tests/core/passes/test_context.py
    - tests/core/passes/test_registry.py
  modified: []

key-decisions:
  - "CompilerContext implemented exactly per PATTERNS.md recommendation: @dataclass(frozen=True, slots=True), fields typed against the three Plan 02 Protocol ports (LLMPort, RepositoryPort, MarkdownParserPort)."
  - "PassRegistry implemented verbatim per PATTERNS.md/RESEARCH.md's load-bearing sketch — register() never inspects depends_on; pipeline() builds the full dependency graph and validates via graphlib.TopologicalSorter, re-raising CycleError with the actual cycle nodes named."
  - "Pass Protocol uses a TYPE_CHECKING-guarded import of CompilerContext to avoid a circular import between base.py and context.py (context.py imports the port Protocols, not base.py)."

requirements-completed: ["CORE-02", "CORE-03", "CORE-04", "CORE-05", "PASS-02", "PASS-05", "EXT-01"]

# Metrics
duration: 12min
completed: 2026-06-30
---

# Phase 1 Plan 3: Pass Registry Mechanics and CompilerContext Summary

**graphlib.TopologicalSorter-based PassRegistry closing ARCHITECTURE.md's comment-only `pipeline()` gap, plus an immutable, explicitly-constructed CompilerContext DI container — both proven via TDD RED/GREEN with a literal EXT-01 no-edit-existing-files proof**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-30T05:30:12Z
- **Completed:** 2026-06-30T05:42:00Z
- **Tasks:** 2
- **Files modified:** 7 (7 created, 0 modified)

## Accomplishments
- `Pass` is a real `typing.Protocol` (`name`, `depends_on`, `__call__(ir, ctx) -> ir`) — cannot be directly instantiated, verified via `pytest.raises(TypeError)`
- `CompilerContext` is a `@dataclass(frozen=True, slots=True)` DI container holding `llm`/`repository`/`parser` (typed against Plan 02's `LLMPort`/`RepositoryPort`/`MarkdownParserPort` Protocols) plus `compiler_version`/`schema_version` — field reassignment raises `FrozenInstanceError`, and every test/run constructs it explicitly (never a module-level global)
- `compiler_version`, `schema_version`, `prompt_version` are importable string constants from `kir.core.config.versions`
- `PassRegistry.register()` never validates `depends_on` (D-02) — registering a pass with an unregistered dependency succeeds silently
- `PassRegistry.pipeline()` builds the dependency graph and validates at build time via `graphlib.TopologicalSorter`: raises `MissingDependencyError` naming the missing pass, or `graphlib.CycleError` naming the actual cycle members
- `pipeline()` returns passes in a valid topological order proven via index-comparison (not exact list equality, since ties are not unique)
- EXT-01 proof: a brand-new pass defined entirely inside `test_registry.py` registers and appears correctly ordered in `pipeline()`'s output without editing `registry.py`, `base.py`, or `context.py`
- Full test suite: 55 tests pass (`uv run pytest -q`), exit code 0 (45 from Plan 02 + 10 new this plan)

## Task Commits

Each task followed the TDD RED -> GREEN cycle, committed atomically:

1. **Task 1: Pass Protocol, CompilerContext, and version constants**
   - RED: `b47dced` (test) — failing tests for Pass Protocol non-instantiability, CompilerContext construction/frozen/readability, version constants
   - GREEN: `1cdf69f` (feat) — `base.py`, `context.py`, `versions.py` implemented, all 5 tests pass
2. **Task 2: PassRegistry with graphlib-based topological pipeline**
   - RED: `b29bfa0` (test) — failing tests for D-02 build-time-only validation, missing-dependency/cycle detection, dependency ordering, EXT-01 proof
   - GREEN: `9453db7` (feat) — `registry.py` implemented, all 5 tests pass

**Plan metadata:** (final commit pending below)

## Files Created/Modified
- `src/kir/core/passes/base.py` - `Pass` Protocol (`name`, `depends_on`, `__call__(ir, ctx) -> ir`), `TYPE_CHECKING`-guarded forward ref to `CompilerContext`
- `src/kir/core/passes/context.py` - `CompilerContext` frozen+slotted dataclass DI container
- `src/kir/core/passes/registry.py` - `MissingDependencyError`, `PassRegistry` (`register()`, `pipeline()`)
- `src/kir/core/config/versions.py` - `compiler_version`, `schema_version`, `prompt_version` constants
- `tests/core/passes/test_base.py` - Pass Protocol non-instantiability test
- `tests/core/passes/test_context.py` - CompilerContext construction/frozen/readability tests, version-constant import tests
- `tests/core/passes/test_registry.py` - D-02, missing-dependency, cycle, dependency-order, and EXT-01 proof tests

## Decisions Made
- `CompilerContext` built exactly per PATTERNS.md's explicit recommendation: `@dataclass(frozen=True, slots=True)`, not Pydantic — Protocol-typed port fields and no serialization need
- `PassRegistry` implemented verbatim per PATTERNS.md/RESEARCH.md's load-bearing sketch (the single largest concrete gap RESEARCH.md flagged: ARCHITECTURE.md's own `pipeline()` sketch was comment-only)
- `Pass` Protocol uses a `TYPE_CHECKING`-guarded import for `CompilerContext` to avoid a circular import (base.py <-> context.py)

## Deviations from Plan

None - plan executed exactly as written. All file paths, behaviors, and the TDD RED/GREEN sequence from the plan were followed verbatim.

## TDD Gate Compliance

Both tasks followed the mandatory RED -> GREEN sequence, confirmed in git log:
- Task 1: `b47dced` (test, RED) -> `1cdf69f` (feat, GREEN)
- Task 2: `b29bfa0` (test, RED) -> `9453db7` (feat, GREEN)

No REFACTOR commits were needed — both GREEN implementations matched PATTERNS.md's verbatim sketches with no follow-up cleanup required.

## Issues Encountered

None.

## User Setup Required

None - pure pass-mechanics/DI-container code, no external service configuration required.

## Next Phase Readiness
- Every real compiler pass (Phase 2+) can now self-register via `PassRegistry.register()` and be ordered via `pipeline()` without touching `registry.py`/`base.py`/`context.py`
- `CompilerContext` is ready to be constructed once per test/run in Plan 04's `conftest.py` fixtures (`fake_compiler_context`, `fake_registry`) and threaded through every pass call
- `kir.core.config.versions` constants are ready for Phase 2's prompt-versioning and cache-key-construction needs (`prompt_version` pre-declared, unused until then)
- No blockers

---
*Phase: 01-compiler-foundation*
*Completed: 2026-06-30*

## Self-Check: PASSED

All 7 created source/test files and this SUMMARY.md verified present on disk. All 4 task commit hashes (b47dced, 1cdf69f, b29bfa0, 9453db7) plus the SUMMARY commit (65a269a) verified present in git log.
