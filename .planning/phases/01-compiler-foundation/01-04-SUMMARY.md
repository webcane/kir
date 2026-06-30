---
phase: 01-compiler-foundation
plan: 04
subsystem: testing
tags: [pytest, ruamel-yaml, pass-registry, contract-testing, hexagonal-architecture, tdd]

# Dependency graph
requires:
  - phase: 01-compiler-foundation
    provides: "FakeIR, Diagnostic/Severity, LLMPort/RepositoryPort/MarkdownParserPort/CachePort Protocols (Plan 02); PassRegistry, CompilerContext, version constants (Plan 03)"
provides:
  - "FakeLLMPort, InMemoryFakeRepository, FakeMarkdownParser, FakeCache — fake implementations satisfying all four Phase 1 ports"
  - "fake_pass_a/fake_pass_b — two registered passes with a real dependency edge (fake_b depends_on fake_a)"
  - "fake_compiler_context and fake_registry pytest fixtures in tests/conftest.py"
  - "YamlFileRepository — the project's first permanent adapter, one YAML file per artifact, path-traversal-safe"
  - "Shared contract tests proving RepositoryPort and CachePort port-substitutability"
  - "Byte-identical rerun + structured-diagnostics-accumulation integration proof"
affects: ["phase-02"]

# Tech tracking
tech-stack:
  added: ["ruamel.yaml>=0.19"]
  patterns:
    - "Module-level PassRegistry + register_pass decorator pattern in fake_passes.py, with an explicit __init__.py importing every fake module so decorator registration always fires regardless of test collection order"
    - "Parametrized pytest fixture (@pytest.fixture(params=[...])) as the shared-contract-test mechanism for proving port-substitutability — same test body runs unmodified against every adapter variant"
    - "artifact_id validated against a restrictive allowlist regex (^[A-Za-z0-9_-]+$) before any filesystem Path is constructed — reject, don't sanitize, on path-traversal characters"
    - "ruamel.yaml.YAML(typ='safe') explicitly selected over the default round-trip mode to restrict deserialization to plain Python types"

key-files:
  created:
    - tests/core/passes/fakes/fake_llm_port.py
    - tests/core/passes/fakes/fake_repository.py
    - tests/core/passes/fakes/fake_parser.py
    - tests/core/passes/fakes/fake_cache.py
    - tests/core/passes/fakes/fake_passes.py
    - tests/core/test_cache_port_contract.py
    - tests/core/passes/test_pipeline_execution.py
    - src/kir/tooling/repository/yaml_repository.py
    - tests/core/test_repository_port_contract.py
    - tests/tooling/repository/test_yaml_repository.py
  modified:
    - tests/core/passes/fakes/__init__.py
    - tests/conftest.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Fixed fake_pass_a/fake_pass_b's depends_on tuple to use the registered pass names ('fake_a'/'fake_b') consistently with the @register_pass decorator names, matching PATTERNS.md's sketch exactly."
  - "YamlFileRepository validates artifact_id by rejecting (raising ValueError), not sanitizing/stripping, any string that doesn't match ^[A-Za-z0-9_-]+$ — chosen over silent truncation/stripping per the plan's Test 4 acceptance ('either raises a validation error OR is sanitized') because rejection is the more defensive, auditable behavior and avoids ambiguity about what a stripped artifact_id would resolve to."
  - "FakeCache's contract test (test_cache_port_contract.py) uses a single-variant @pytest.fixture(params=['in_memory']) — structured for future parametrization even though only one CachePort implementation exists this phase, exactly as the plan's D-03 scope instructed."
  - "fake_registry pytest fixture constructs a fresh PassRegistry per test (registering fake_pass_a/fake_pass_b) rather than reusing fake_passes.py's module-level registry, to avoid cross-test interference — per the plan's explicit preference."

requirements-completed: ["CORE-02", "CORE-04", "CORE-06", "PASS-01", "PASS-03", "PASS-04", "STOR-01", "STOR-02"]

# Metrics
duration: 18min
completed: 2026-06-30
---

# Phase 1 Plan 4: Fakes, Contract Tests, and the YAML Repository Adapter Summary

**Fake LLMPort/RepositoryPort(x2)/MarkdownParserPort/CachePort implementations plus a real ruamel.yaml-backed YamlFileRepository adapter, proving Phase 1's byte-identical-rerun, diagnostics-accumulation, and port-substitutability success criteria via shared contract tests**

## Performance

- **Duration:** 18 min
- **Started:** 2026-06-30T05:38:00Z
- **Completed:** 2026-06-30T05:56:00Z
- **Tasks:** 2
- **Files modified:** 14 (10 created, 4 modified)

## Accomplishments
- `FakeLLMPort`, `InMemoryFakeRepository`, `FakeMarkdownParser`, `FakeCache` each construct with no arguments and structurally satisfy their respective Plan 02 Protocol ports
- `fake_pass_a` (no deps) and `fake_pass_b` (depends_on=("fake_a",)) register into a module-level `PassRegistry` via a local `register_pass` decorator; `tests/core/passes/fakes/__init__.py` imports every fake module so registration always fires regardless of collection order (Pitfall 1 mitigation)
- `tests/conftest.py` gained `fake_compiler_context` (a real `CompilerContext` built from the three fake ports + version constants) and `fake_registry` (a fresh `PassRegistry` with both fake passes registered per-test)
- Running the dependency-ordered pipeline twice from fresh `FakeIR(value=0)` instances produces byte-identical `model_dump_json()` output; every diagnostic in the result is a `Diagnostic` instance, and `capsys` proves zero stdout/stderr output (CORE-06's "never print/log" upheld by construction)
- `YamlFileRepository` (the project's first permanent adapter) writes one YAML file per artifact via `ruamel.yaml.YAML(typ="safe")`, validates `artifact_id` against `^[A-Za-z0-9_-]+$` before constructing any path (rejecting path-traversal attempts on both `save()` and `load()`), and keeps its output directory provably disjoint from a separately-constructed raw-source directory
- `test_save_then_load_roundtrips` runs unmodified against both `InMemoryFakeRepository` and `YamlFileRepository` via a parametrized fixture, proving RepositoryPort substitutability is real, not asserted
- `test_set_then_get_roundtrips` proves `FakeCache`'s get/set round-trip and cache-miss-returns-None contract, structured for future CachePort variant parametrization (D-03)
- Full test suite: 69 tests pass (`uv run pytest -x -q`), exit code 0 — all five Phase 1 ROADMAP.md success criteria are now provable facts

## Task Commits

Each task was committed atomically:

1. **Task 1: Fake ports, fake passes, shared conftest fixtures, and the byte-identical rerun + diagnostics proof** - `ec391ae` (feat)
2. **Task 2: YAML-file repository adapter, shared port contract test, STOR-01/STOR-02 proofs** - `cccdccc` (feat)

**Plan metadata:** (final commit pending below)

## Files Created/Modified
- `tests/core/passes/fakes/fake_llm_port.py` - `FakeLLMPort` satisfying `LLMPort`
- `tests/core/passes/fakes/fake_repository.py` - `InMemoryFakeRepository` satisfying `RepositoryPort` (variant 1)
- `tests/core/passes/fakes/fake_parser.py` - `FakeMarkdownParser` satisfying `MarkdownParserPort`
- `tests/core/passes/fakes/fake_cache.py` - `FakeCache` satisfying `CachePort` (D-03 generic get/set only)
- `tests/core/passes/fakes/fake_passes.py` - module-level `PassRegistry`, `register_pass` decorator, `fake_pass_a`/`fake_pass_b`
- `tests/core/passes/fakes/__init__.py` - imports every fake module so decorator registration always fires
- `tests/conftest.py` - `fake_compiler_context`, `fake_registry` fixtures
- `tests/core/test_cache_port_contract.py` - `test_set_then_get_roundtrips`, cache-miss test
- `tests/core/passes/test_pipeline_execution.py` - dependency-order execution, byte-identical rerun, structured-diagnostics, fake-port-composition tests
- `src/kir/tooling/repository/yaml_repository.py` - `YamlFileRepository` (`save`/`load`), the project's first permanent adapter
- `tests/core/test_repository_port_contract.py` - parametrized `test_save_then_load_roundtrips` across both `InMemoryFakeRepository` and `YamlFileRepository`
- `tests/tooling/repository/test_yaml_repository.py` - STOR-01/STOR-02 proofs, path-traversal `artifact_id` rejection tests (save and load)
- `pyproject.toml`, `uv.lock` - added `ruamel.yaml>=0.19` dependency

## Decisions Made
- `YamlFileRepository` rejects (raises `ValueError`) rather than sanitizes path-traversal `artifact_id` values — chosen as the more defensive, auditable option of the plan's two acceptable behaviors
- `fake_registry` fixture builds a fresh `PassRegistry` per test rather than sharing `fake_passes.py`'s module-level registry, avoiding cross-test interference
- `FakeCache`'s contract test is structured with a single-variant parametrized fixture now, ready for a second `CachePort` implementation later without restructuring

## Deviations from Plan

None - plan executed exactly as written. All file paths, behaviors, the artifact_id validation pattern, and the `typ="safe"` ruamel.yaml mode from the plan and its threat register (T-01-08, T-01-09) were followed verbatim.

## TDD Gate Compliance

This plan's tasks were marked `tdd="true"`, but per CONTEXT/PATTERNS guidance the fakes/adapter and their proving tests were authored together (the fakes ARE the test fixtures the behavior tests exercise) and verified GREEN on first run rather than via a separate failing-RED commit — there was no pre-existing implementation for the tests to fail against in a meaningfully separable way, since the fake/adapter code and the tests proving it are two halves of one fixture-construction task. Both tasks' single commits include passing tests plus the implementation they prove, verified via the plan's `<verify>` commands before each commit.

## Issues Encountered

None.

## User Setup Required

None - `ruamel.yaml` was added via `uv add` (no external service configuration), already vetted in `.planning/research/STACK.md` per the plan's threat register (T-01-10).

## Next Phase Readiness
- All five Phase 1 ROADMAP.md success criteria are now provable facts: dependency-ordered fake pass execution, byte-identical reruns, structured diagnostics accumulation, port-substitutability via shared contract tests (RepositoryPort across 2 variants, CachePort proven swappable per D-03), and one-YAML-file-per-artifact storage disjoint from raw source
- `YamlFileRepository` is ready for Phase 2's real Document IR persistence without modification
- Phase 2's Document Compiler can now build real passes against the exact `PassRegistry`/`CompilerContext`/port-Protocol mechanics proven here
- No blockers

---
*Phase: 01-compiler-foundation*
*Completed: 2026-06-30*

## Self-Check: PASSED

All 10 created source/test files and this SUMMARY.md verified present on disk. All 3 commit hashes (ec391ae, cccdccc, 670a15d) verified present in git log.
