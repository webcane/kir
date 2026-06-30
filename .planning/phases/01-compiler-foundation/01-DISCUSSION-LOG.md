# Phase 1: Compiler Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-30
**Phase:** 1-Compiler Foundation
**Areas discussed:** Diagnostics behavior, Dependency graph failure mode, Cache abstraction scope, Artifact Manifest scope

---

## Diagnostics behavior (CORE-06)

| Option | Description | Selected |
|--------|-------------|----------|
| Always run all passes | Rust-compiler-style: collect diagnostics from every pass regardless of severity; halt is the caller's decision after the full run | ✓ |
| Halt on first Error | Pipeline stops executing further passes as soon as any pass returns an Error diagnostic | |
| Pass-declared | Each pass declares itself as halt-on-error or continue-on-error | |

**User's choice:** Always run all passes (Recommended option)
**Notes:** None — accepted the recommendation as presented.

---

## Dependency graph failure mode (CORE-04 / PASS-05)

| Option | Description | Selected |
|--------|-------------|----------|
| At pipeline-build time | registry.pipeline() runs the topological sort and raises immediately on cycle/unresolvable depends_on; registration stays cheap/order-independent | ✓ |
| At registration time | register_pass() validates depends_on against already-registered passes immediately | |

**User's choice:** At pipeline-build time (Recommended option)
**Notes:** None — accepted the recommendation as presented.

---

## Cache abstraction scope

| Option | Description | Selected |
|--------|-------------|----------|
| Generic key-value only | Cache Protocol is just get(key)/set(key, value) over opaque string keys; Phase 2's LLM cache builds key construction on top | ✓ |
| Pre-shaped for LLM cache keys | Cache Protocol's key type already models the (checksum, prompt_version, schema_version, model_id) tuple | |

**User's choice:** Generic key-value only (Recommended option)
**Notes:** None — accepted the recommendation as presented.

---

## Artifact Manifest scope

| Option | Description | Selected |
|--------|-------------|----------|
| Artifact id + version only | Minimal manifest proving the mechanism works with fakes; checksums/dependency tracking deferred to Phase 5 | ✓ |
| Id + version + checksum + dependencies | Build the fuller incremental-compilation shape now | |

**User's choice:** Artifact id + version only (Recommended option)
**Notes:** None — accepted the recommendation as presented.

---

## Claude's Discretion

- Exact module/file layout within the 5-package split (`core`, `compiler/documents`, `compiler/knowledge`, `llm`, `tooling`) — follows `.planning/research/ARCHITECTURE.md` unless planning surfaces a conflict.
- Exact set of fake passes/adapters used to demonstrate the mechanics — left to research/planning, bounded by ROADMAP.md's Phase 1 success criteria.

## Deferred Ideas

None — discussion stayed within phase scope. LLM-specific cache-key shape and incremental-compilation manifest fields were discussed as explicit non-goals for Phase 1 (already scoped to Phase 2 and Phase 5 respectively in ROADMAP.md), not new scope-creep ideas.
