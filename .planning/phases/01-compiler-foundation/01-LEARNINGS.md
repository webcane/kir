---
phase: 1
phase_name: "Compiler Foundation"
project: "KIR"
generated: "2026-07-01"
counts:
  decisions: 11
  lessons: 4
  patterns: 9
  surprises: 4
missing_artifacts:
  - "01-UAT.md"
---

# Phase 1 Learnings: Compiler Foundation

## Decisions

### CompilerContext as frozen dataclass, not Pydantic

`CompilerContext` was implemented as `@dataclass(frozen=True, slots=True)` rather than a `Pydantic BaseModel`. Protocol-typed port fields do not require serialization, and Pydantic adds no value when the type is a DI container never written to YAML or JSON.

**Rationale:** `frozen=True` gives `FrozenInstanceError` on reassignment; `slots=True` reduces memory overhead. Pydantic's `ConfigDict(frozen=True)` would have required marking all port fields as `Arbitrary_types`, complicating downstream usage.
**Source:** 01-03-SUMMARY.md

---

### Pass dependency validation deferred to pipeline(), not register()

`PassRegistry.register()` never validates `depends_on` entries. Validation (missing dependency, cycle detection) happens exclusively at `pipeline()` build time via `graphlib.TopologicalSorter`. This is D-02.

**Rationale:** Allowing registration of passes with unresolved dependencies is necessary for dynamic/plugin-style assembly where passes may be registered in arbitrary order across modules. Failing at pipeline-construction time (not at registration) produces a cleaner error surface.
**Source:** 01-03-SUMMARY.md

---

### TYPE_CHECKING guard for Pass Protocol's CompilerContext import

`base.py`'s `Pass` Protocol uses a `TYPE_CHECKING`-guarded import of `CompilerContext` to avoid a circular import between `base.py` and `context.py`.

**Rationale:** `context.py` imports port Protocols from `core/ports/`; `base.py` needs to reference `CompilerContext` in the `__call__` signature. The `TYPE_CHECKING` guard avoids the cycle without restructuring the module layout. (Note: this is the one exception to the style guide's TYPE_CHECKING prohibition — it resolves a genuine circular import, not a convenience import.)
**Source:** 01-03-SUMMARY.md

---

### YamlFileRepository rejects path-traversal artifact_id, does not sanitize

`YamlFileRepository.save()` and `load()` validate `artifact_id` against `^[A-Za-z0-9_-]+$` and raise `ValueError` on any non-matching string, including path-traversal characters (`../`, `/`, `..`).

**Rationale:** Silent sanitization (e.g., stripping `/` from `"../../etc/passwd"`) is ambiguous — the sanitized id may collide with a legitimate id. Rejection is auditable and deterministic; the caller always knows exactly which artifact was attempted.
**Source:** 01-04-SUMMARY.md

---

### SourceRef lives in models/provenance.py — value_objects.py imports it

`SourceRef` is defined exactly once in `src/kir/core/domain/models/provenance.py`. `value_objects.py` imports it rather than redefining it.

**Rationale:** The plan explicitly required picking one canonical home. Placing SourceRef in provenance.py co-locates it with other provenance-related types (future: DocumentOrigin, ContentHash) and avoids duplication.
**Source:** 01-02-SUMMARY.md

---

### Relation.relation_type stays plain str, not an enum

`Relation.relation_type` is `str`, not an enum. The vocabulary of relation types is core-and-extensible per PROJECT.md Architectural Decisions and will be finalized in Phase 3/M2.

**Rationale:** Locking the vocabulary to an enum now would require editing the domain model every time a new relation type is introduced by a downstream consumer. The open-vocabulary design matches the "Knowledge IR is a compilation target" framing — callers impose domain constraints via their own validation.
**Source:** 01-02-SUMMARY.md

---

### Port-Protocol verification via mro + TypeError, not @runtime_checkable

Protocol conformance in tests is verified via `Protocol in type(obj).__mro__` and `pytest.raises(TypeError)` on direct instantiation, not via `@runtime_checkable` + `isinstance()`.

**Rationale:** `@runtime_checkable` only checks attribute names, not signatures — it will accept any object with a matching attribute name even if the method signature is wrong. The MRO + TypeError pattern proves that the Protocol is a real ABC-style Protocol (not directly instantiable) without relying on the weaker structural check.
**Source:** 01-02-SUMMARY.md

---

### fake_registry fixture builds fresh PassRegistry per test

The `fake_registry` pytest fixture in `tests/conftest.py` constructs a new `PassRegistry` per test (registering `fake_pass_a` and `fake_pass_b`) rather than reusing `fake_passes.py`'s module-level registry.

**Rationale:** Sharing the module-level registry across tests risks cross-test interference if one test modifies registry state. A fresh instance per test is more isolated and less surprising.
**Source:** 01-04-SUMMARY.md

---

### CLI entrypoint removed from uv init scaffolding

`uv init --package` generates a `main()` function and `[project.scripts]` CLI entrypoint. Both were removed from `src/kir/__init__.py` and `pyproject.toml`.

**Rationale:** No CLI exists in Phase 1 (tooling/cli is a later-phase deliverable per ARCHITECTURE.md). Including a stub entrypoint would mislead readers about the current interface surface.
**Source:** 01-01-SUMMARY.md

---

### pytest_sessionfinish hook normalizes exit code 5 to 0 for zero-test baseline

A `pytest_sessionfinish` hook in `tests/conftest.py` converts pytest's `NO_TESTS_COLLECTED` (exit 5) to `OK` (exit 0).

**Rationale:** The plan explicitly required `uv run pytest` to exit 0 with zero tests collected, but pytest's documented behavior is exit 5 in that case. The hook fires only when `exitstatus == ExitCode.NO_TESTS_COLLECTED`, has no effect once real tests exist, and does not mask genuine failures.
**Source:** 01-01-SUMMARY.md

---

### FakeCache contract test uses single-variant parametrized fixture

`test_cache_port_contract.py` uses `@pytest.fixture(params=["in_memory"])` with a single variant, even though only one `CachePort` implementation exists in Phase 1 (D-03 scope limit).

**Rationale:** Structuring for future parametrization now means a second `CachePort` implementation can be added without restructuring the test. The single-variant fixture is functionally identical to a plain fixture but telegraphs the pattern.
**Source:** 01-04-SUMMARY.md

---

## Lessons

### pytest exits with code 5 (not 0) when no tests are collected

Plans that assert `uv run pytest` exits 0 on a zero-test baseline need an explicit fix. pytest's `ExitCode.NO_TESTS_COLLECTED == 5` is documented behavior, not a bug.

**Context:** The plan's acceptance criteria, task done-criteria, and success criteria all said "exit 0." After scaffolding, pytest exited 5. The plan was satisfied by adding a `pytest_sessionfinish` hook — but the mismatch wasn't anticipated in planning.
**Source:** 01-01-SUMMARY.md

---

### CycleError re-raise loses the structured args[1] cycle node list

`PassRegistry.pipeline()` re-raises `CycleError` with a formatted string message, producing a 1-tuple `args`. Any caller that tries to access `.args[1]` (mirroring the graphlib contract) gets `IndexError`, not the cycle node list.

**Context:** The bug was invisible to Phase 1 tests because the cycle test only checks `pytest.raises(CycleError)`, not the structure of `.args`. The fix is to preserve the payload: `raise CycleError(f"Cycle: {exc.args[1]}", exc.args[1]) from exc`, or simply re-raise the original without wrapping.
**Source:** 01-REVIEW.md

---

### Fakes authored with their tests cannot follow strict TDD RED→GREEN

When the fakes ARE the test fixtures (not the SUT), there is no pre-existing implementation for the tests to fail against. The RED commit is meaningless — the fake and the test that proves it are two halves of one fixture-construction task.

**Context:** Plan 04 marked tasks `tdd="true"`, but both tasks' single commits included passing tests plus implementation. This is correct behavior: strict RED→GREEN applies when there is a production implementation to drive out; it collapses when the subject IS a test double.
**Source:** 01-04-SUMMARY.md

---

### Import boundary audit covers only core/domain/, not all of core/

`test_import_boundaries.py` globs `src/kir/core/domain/**/*.py`. The `core/passes/` and `core/ports/` subtrees are currently clean (verified manually) but have no automated guard against drift.

**Context:** CORE-01's literal text says "Domain model has zero import-level dependency on LLM/filesystem/YAML." The audit is technically complete against the literal requirement. But the spirit in CLAUDE.md includes passes and ports — extend the glob to `src/kir/core/` in a later phase.
**Source:** 01-REVIEW.md

---

## Patterns

### Frozen Pydantic domain models with tuple accumulating fields

Every domain model uses `ConfigDict(frozen=True, extra="forbid")`. All accumulating fields use `tuple[T, ...]`, never `list[T, ...]`.

**When to use:** All domain IR types (Document, Concept, Relation, Taxonomy, Conflict, Diagnostic). `frozen=True` prevents mutation; `extra="forbid"` prevents silent field expansion. `tuple` is required because `list` remains appendable even on a frozen model — the tuple invariant makes immutability real, not nominal.
**Source:** 01-02-SUMMARY.md

---

### graphlib.TopologicalSorter for pass dependency ordering

Pass ordering and cycle detection use `graphlib.TopologicalSorter` from the Python stdlib. No hand-rolled DFS.

**When to use:** Any pass registry that needs topological ordering with cycle detection. `graphlib` is stdlib (Python 3.9+), produces deterministic output with `static_order()`, and raises `CycleError` with the cycle members named.
**Source:** 01-03-SUMMARY.md

---

### Module-level registry + explicit __init__.py force-imports for decorator registration

A module-level `PassRegistry` + `register_pass` decorator pattern in `fake_passes.py` (and later `passes/__init__.py`) is paired with an explicit `__init__.py` that imports every pass module, ensuring decorators fire regardless of test collection order.

**When to use:** Any PassRegistry where passes self-register via a decorator. Without the explicit imports, pytest's collection order determines which passes are registered — a fragile, ordering-dependent state.
**Source:** 01-04-SUMMARY.md

---

### Parametrized pytest fixture for shared port-contract tests

A `@pytest.fixture(params=[...])` fixture is the idiomatic way to prove port substitutability — the same test body runs unmodified against every adapter variant.

**When to use:** Any RepositoryPort, CachePort, or future Port with multiple implementations. `params=["variant_a", "variant_b"]` makes the test matrix explicit and avoids duplicating test logic.
**Source:** 01-04-SUMMARY.md

---

### AST-based import boundary audit

Import boundary enforcement uses `ast.parse()` to walk the source tree, not `grep` or regex. This catches aliased imports (`import yaml as y`) and dynamic imports that grep misses.

**When to use:** Any import-boundary enforcement rule (CORE-01 or future cross-layer guards). Regex/grep produces false negatives on aliased or starred imports.
**Source:** 01-02-SUMMARY.md

---

### artifact_id allowlist validation before filesystem Path construction

`YamlFileRepository` validates `artifact_id` against `^[A-Za-z0-9_-]+$` before constructing any `Path`. The pattern is an allowlist (safe characters), not a denylist (dangerous characters) — reject if not in the set, not if in a bad set.

**When to use:** Any user-controlled string that becomes a filesystem path component. Allowlist is safer than denylist — unknown attack vectors pass denylists but fail allowlists.
**Source:** 01-04-SUMMARY.md

---

### ruamel.yaml YAML(typ='safe') for YAML serialization

`ruamel.yaml.YAML(typ="safe")` was explicitly selected over the default round-trip mode for `YamlFileRepository`.

**When to use:** Any YAML deserialization that doesn't need round-trip comment preservation. `typ="safe"` restricts output to plain Python types (dict/list/str/int/float/bool/None), blocking YAML's arbitrary-object-instantiation attack surface.
**Source:** 01-04-SUMMARY.md

---

### TDD RED→GREEN proven via commit hashes in SUMMARY.md

Plan 03 documented the RED commit hash (failing test) and GREEN commit hash (implementation) for both tasks. This makes the TDD gate verifiable via `git log`, not just claimed in prose.

**When to use:** Any TDD-mandated plan. Recording both commit hashes in the SUMMARY gives the verifier a concrete artifact to check, not a self-attestation.
**Source:** 01-03-SUMMARY.md

---

### FakeIR decoupled from real domain models

`FakeIR` in `src/kir/core/domain/ir.py` is a minimal Pydantic model with no inheritance from `Document`, `Concept`, or any real IR type.

**When to use:** Pass mechanics tests (registry ordering, pipeline execution, diagnostics accumulation) that don't need the full domain schema. Decoupling keeps pass-mechanics tests insulated from domain model schema changes.
**Source:** 01-02-SUMMARY.md

---

## Surprises

### pytest exit code 5 contradicts "exit 0" plan requirements

The plan's explicit acceptance criterion (`uv run pytest` exits 0 with zero tests) collided with pytest's documented behavior (exit 5 for no tests collected). This required a `pytest_sessionfinish` hook that wasn't in the original plan.

**Impact:** One unanticipated file modification (`tests/conftest.py`) and one auto-fixed deviation. Low impact — the hook is scoped and has no effect post-Wave-0. Future plan criteria should say "exit 0 or NO_TESTS_COLLECTED" or simply not test exit codes on a zero-test baseline.
**Source:** 01-01-SUMMARY.md

---

### CycleError re-raise silently breaks args[1] contract — no test caught it

`registry.py`'s `CycleError` re-raise was a correctness bug (structured node list lost) but was invisible to the test suite because no test inspects `.args[1]`. The bug was found only in the code review.

**Impact:** The D-02 test (`test_circular_dependency_detected_at_pipeline_build_time`) catches the exception type but not the payload. Any future caller that programmatically extracts cycle nodes will get `IndexError`. Low blast radius now, but worth noting that cycle exception tests should assert on `.args[1]` content, not just the exception type.
**Source:** 01-REVIEW.md

---

### TYPE_CHECKING coupling in fake_llm_port.py creates hidden runtime risk

`fake_llm_port.py` has both `from __future__ import annotations` and `if TYPE_CHECKING:` imports. Removing `__future__` without also removing `TYPE_CHECKING` causes a `NameError` at runtime — the two are co-dependent in this file.

**Impact:** This is a style-guide violation that can't be cleanly fixed by removing either guard in isolation. It requires removing both simultaneously. Flagged as tech debt in the Phase 1 review — cleanup is blocked until Phase 1 style debt is addressed.
**Source:** 01-VERIFICATION.md (tech debt section)

---

### Phase 1 executed in ~70 minutes total across 4 plans

All four Phase 1 plans completed in 15 + 25 + 12 + 18 = 70 minutes of execution time, with zero deviations in Plans 02, 03, and 04 and one auto-fixed deviation in Plan 01.

**Impact:** Planning artifacts (RESEARCH.md, PATTERNS.md, ARCHITECTURE.md sketches) were thorough enough that execution was near-scripted. This suggests the pre-phase research + discussion investment paid off in dramatically reduced execution variance.
**Source:** 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md

---

_Phase: 01-compiler-foundation_
_Generated: 2026-07-01_
_Source artifacts: 01-01..04-SUMMARY.md, 01-REVIEW.md, 01-VERIFICATION.md_
