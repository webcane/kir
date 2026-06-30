---
phase: 1
slug: compiler-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (per STACK.md; not yet installed — greenfield repo) |
| **Config file** | none yet — Wave 0 must create `pyproject.toml` with `[tool.pytest.ini_options]` and a `tests/` root |
| **Quick run command** | `uv run pytest tests/core -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds (small, fast unit-only suite at this phase) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/core -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD-01 | TBD | 0 | CORE-01 | — | Domain has zero LLM/filesystem/YAML imports | unit (static analysis) | `pytest tests/core/test_import_boundaries.py -x` | ❌ W0 | ⬜ pending |
| TBD-02 | TBD | TBD | CORE-02 | — | Ports are typed Protocols satisfied structurally by adapters | unit | `pytest tests/core/ports/ -x` | ❌ W0 | ⬜ pending |
| TBD-03 | TBD | TBD | CORE-03 | — | Passes self-register via decorator without editing existing files | unit | `pytest tests/core/passes/test_registry.py::test_new_pass_registers_without_editing_existing -x` | ❌ W0 | ⬜ pending |
| TBD-04 | TBD | TBD | CORE-04 | — | Pipeline executes passes in dependency-declared order | unit | `pytest tests/core/passes/test_registry.py::test_pipeline_orders_by_dependency -x` | ❌ W0 | ⬜ pending |
| TBD-05 | TBD | TBD | CORE-05 | — | All passes execute inside shared immutable CompilerContext | unit | `pytest tests/core/passes/test_context.py -x` | ❌ W0 | ⬜ pending |
| TBD-06 | TBD | TBD | CORE-06 | — | Every pass returns structured Diagnostics, never prints/logs; pipeline always runs all passes regardless of severity (D-01) | unit | `pytest tests/core/passes/test_pipeline_execution.py::test_diagnostics_are_structured -x` | ❌ W0 | ⬜ pending |
| TBD-07 | TBD | TBD | CORE-07 | — | Passes never mutate IR in place; produce new immutable artifact | unit | `pytest tests/core/domain/test_immutability.py -x` | ❌ W0 | ⬜ pending |
| TBD-08 | TBD | TBD | PASS-01..05 | — | Pass contract (one-in-one-out, isolated, registry-ordered, no side-channel comms); dependency-graph errors (cycle/missing) raised at pipeline-build time (D-02) | unit | `pytest tests/core/passes/ -x` | ❌ W0 | ⬜ pending |
| TBD-09 | TBD | TBD | EXT-01 | — | New pass addable without modifying core pipeline file | unit | `pytest tests/core/passes/test_registry.py::test_new_pass_registers_without_editing_existing -x` | ❌ W0 | ⬜ pending |
| TBD-10 | TBD | TBD | STOR-01 | — | One YAML file per artifact, no monolithic JSON | unit (filesystem, `tmp_path`) | `pytest tests/tooling/repository/test_yaml_repository.py::test_one_file_per_artifact -x` | ❌ W0 | ⬜ pending |
| TBD-11 | TBD | TBD | STOR-02 | — | Output directory separate from raw source directory | unit (filesystem, `tmp_path`) | `pytest tests/tooling/repository/test_yaml_repository.py::test_output_dir_disjoint_from_raw -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs/plan/wave columns are TBD until the planner assigns concrete plan/task IDs — this table's requirement→test mapping is the binding contract; the planner fills in IDs.*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` with `[tool.pytest.ini_options]`, `src/` layout declared, pydantic/pytest dependencies — project does not exist yet (confirmed greenfield)
- [ ] `tests/conftest.py` — shared fixtures: `fake_compiler_context`, `fake_registry`, `tmp_path`-based repository fixture
- [ ] `tests/core/passes/fakes/__init__.py` — explicit import list to trigger fake-pass decorator registration (import-order self-registration pitfall mitigation)
- [ ] Framework install: `uv add --dev pytest` and `uv add pydantic` — no test framework or dependency currently installed anywhere in the repo

*(All gaps listed — this is a from-scratch project, so the entire test infrastructure is a Wave 0 deliverable, not a partial gap.)*

---

## Manual-Only Verifications

*None — all Phase 1 behaviors (domain import boundaries, registry/pipeline ordering, diagnostics accumulation, port-fake swappability, one-file-per-artifact repository output) have automated verification per the table above.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (mapped above; planner assigns concrete task IDs)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every requirement maps to an automated pytest command)
- [x] Wave 0 covers all MISSING references (pyproject.toml, conftest.py, fakes `__init__.py`, framework install all listed)
- [x] No watch-mode flags (`-x -q`, no `--watch`)
- [x] Feedback latency < 10s (small unit-only suite at this phase)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
