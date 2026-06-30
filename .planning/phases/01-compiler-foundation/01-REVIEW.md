---
phase: 01-compiler-foundation
status: issues_found
files_reviewed: 58
findings:
  critical: 0
  warning: 1
  info: 4
  total: 5
---

# Phase 1 Code Review

Phase 1's infrastructure substrate (domain models, ports, pass registry/pipeline, cache abstraction, artifact manifest, YAML repository adapter) is in good shape overall. The full test suite (69 tests) passes. Hexagonal boundaries are respected — `core/domain` has zero LLM/filesystem/YAML imports (verified both by the project's own `test_import_boundaries.py` and manually), `core/` never imports `tooling/`, and passes communicate only through `model_copy`-produced IR plus the registry, never via direct cross-pass imports. All locked decisions (D-01 through D-04) are correctly implemented: diagnostics accumulate without halting, dependency-graph validation happens only at `pipeline()` build time (not `register()`), the Cache Protocol stays generic (no LLM-specific cache-key concepts), and `ArtifactManifest` is minimal (id + version only). Immutability is correctly enforced throughout via `frozen=True` + tuple-typed accumulating fields, and the YAML repository adapter validates `artifact_id` against an allowlist regex before constructing any filesystem path, closing the path-traversal vector RESEARCH.md flagged.

One real bug was found in the registry's cycle-error re-raise. The remaining items are minor code-quality notes.

## Warnings

### WR-01: `PassRegistry.pipeline()` re-raises `CycleError` in a way that loses the documented `.args[1]` cycle-node-list contract
**File:** `src/kir/core/passes/registry.py`, lines 47–51

```python
except CycleError as exc:
    # exc.args[1] is the list of nodes forming the cycle (CPython docs)
    raise CycleError(
        f"Circular pass dependency detected: {exc.args[1]}"
    ) from exc
return [self._passes[name] for name in ordered_names]
```

The comment correctly states that `graphlib.CycleError.args[1]` holds the cycle's node list (confirmed: `TopologicalSorter({'a': {'b'}, 'b': {'a'}}).static_order()` raises `CycleError` with `args == ('nodes are in a cycle', ['a', 'b', 'a'])`). But the re-raise constructs a *new* `CycleError` with a single formatted string as its only argument, so the re-raised exception's `args` is a 1-tuple — `exc.args[1]` on the *re-raised* exception now raises `IndexError`, not the cycle list. Verified directly:

```
>>> r.pipeline()
CycleError: ("Circular pass dependency detected: ['a', 'b', 'a']",)
>>> len(e.args)
1
>>> e.args[1]
IndexError: tuple index out of range
```

This doesn't break Phase 1's own tests (`test_circular_dependency_detected_at_pipeline_build_time` only checks `pytest.raises(CycleError)`, not `.args[1]`), but it silently breaks the exact contract D-02 asks for ("a single clear error naming the cycle") for any caller that tries to programmatically extract the cycle nodes from the raised exception — they'd get a formatted string instead of the structured list the docstring promises, and a naive attempt to access `.args[1]` (mirroring the original `graphlib` contract) would crash with `IndexError` instead of returning the cycle.

**Fix:** preserve the structured payload, e.g. `raise CycleError(f"Circular pass dependency detected: {exc.args[1]}", exc.args[1]) from exc`, or simply don't re-wrap — let the original `CycleError` propagate (it already contains a usable message and the correct `.args[1]`).

## Info

### IN-01: Dead code — unused `_DiagnosticsHolder` class in `test_diagnostic.py`
**File:** `tests/core/domain/test_diagnostic.py`, lines 36–41

`_DiagnosticsHolder` is defined with a docstring claiming it's "used only to prove tuple-not-list storage behavior," but it is never instantiated or referenced anywhere — the actual test (`test_diagnostic_accumulating_field_is_stored_as_tuple`, lines 44–54) defines and uses its own local Pydantic `Holder` model instead. This is leftover/dead code from an earlier draft and should be removed.

### IN-02: No empty-string / format validation on identifier-bearing value objects
**Files:** `src/kir/core/domain/value_objects.py` (`ConceptId`, `RelationId`), `src/kir/core/domain/models/document.py` (`Document.id`), `src/kir/core/domain/models/conflict.py` (`Conflict.id`)

`ConceptId(value="")`, `ConceptId(value="../../etc/passwd")`, and `Document(id="")` all construct without error — there is no `min_length` or pattern constraint on any identifier field. This is consistent with Phase 1's stated scope (CONTEXT.md explicitly defers richer invariants to later phases, and the one place an identifier actually reaches a filesystem path — `YamlFileRepository`'s `artifact_id` parameter — does validate against `^[A-Za-z0-9_-]+$`), so this is not a blocking issue. Flagging only so it isn't silently forgotten once `ConceptId`/`Document.id` values start flowing into contexts (cache keys, future filenames, joins) where an empty or malformed identifier would be a real correctness problem.

### IN-03: `core.domain` import-boundary test only scans `src/kir/core/domain`, not all of `core/`
**File:** `tests/core/test_import_boundaries.py`, line 36

`test_domain_has_no_forbidden_imports` globs `Path("src/kir/core/domain").rglob("*.py")`. This matches CORE-01's literal text ("Domain model has zero import-level dependency...") and is what RESEARCH.md's own code example does, so it is not a defect against the locked requirement. However, `core/passes/` and `core/ports/` are equally part of the "no LLM SDK / filesystem / YAML" hexagonal-boundary spirit described in CLAUDE.md's "Layer Boundaries," and currently have no equivalent automated check (they happen to be clean today — verified manually, no forbidden imports present — but nothing prevents drift). Consider widening the glob to `src/kir/core` in a later phase if `passes/`/`ports/` start growing real logic.

### IN-04: `MissingDependencyError` validation only checks declared deps against registered names, not transitively-missing self-deps
**File:** `src/kir/core/passes/registry.py`, lines 34–43

Minor robustness note, not a bug: `pipeline()` builds `graph[name] = set(p.depends_on)` from `self._passes.items()`, so a pass cannot accidentally end up missing from `graph` even if its `depends_on` is empty — this is correct. The only gap is that nothing prevents a pass from declaring `depends_on=(self_name,)` (a pass depending on itself); `graphlib.TopologicalSorter` does correctly raise `CycleError` for this case (a self-loop is a 1-node cycle), so behavior is already correct — this is purely a documentation note: the registry's docstring talks about "missing pass or the cycle members" but doesn't explicitly call out self-dependency as a covered case. No code change needed; noting for completeness only.
