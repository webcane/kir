# Milestone v1.0 — Project Summary

**Generated:** 2026-07-01
**Purpose:** Team onboarding and project review
**Milestone:** M1 — Deterministic Document Compiler (Phases 1, 2, 2.1 of 6 total v1 phases)

---

## 1. Project Overview

KIR (Knowledge Intermediate Representation) is a **semantic compiler**, not a wiki, note-taking app, graph database, or search index. It transforms heterogeneous raw sources — starting with Markdown — into a canonical, deterministic, provenance-tracked Knowledge IR. The mental model is explicit in the project's own framing: "LLVM, but for knowledge" — a stable intermediate representation produced by a pipeline of independently testable compiler passes.

**Core value proposition:** given identical raw sources, compiler version, prompt version, and schema version, KIR must deterministically compile raw Markdown into a canonical Knowledge IR that merges concepts/relations/taxonomy across documents, preserves full provenance, and explicitly records — never silently resolves — semantic conflicts.

**Product boundary:** KIR's public API ends at Knowledge IR. Rendering, synchronization into Logseq/Obsidian/Notion, search indexing, and vector/graph DB serving are all explicitly out of scope and belong to downstream consumers.

**Milestone status:** M1 is **complete**. All three phases (1, 2, and an inserted gap-closure phase 2.1) are done, verified, and cross-audited. This milestone built the bottom half of the system: the compiler substrate (domain model, ports, pass registry) and the first concrete compiler — Markdown → Document IR, including one LLM-backed extraction pass. The next milestone (M2 — Canonical Knowledge Compiler) begins the multi-document merge work (aliases, canonical concepts, relations, taxonomy, conflict detection) and is not yet phase-planned.

---

## 2. Architecture & Technical Decisions

**Foundational architecture (from PROJECT.md, unchanged during M1):**
- Hexagonal architecture — domain model has zero import-level dependency on LLM SDKs, filesystem, or YAML libraries; adapters depend on the domain, never the reverse.
- Pydantic v2 as the canonical IR representation — frozen, `extra="forbid"` models throughout, tuples (not lists) for accumulating fields to make immutability real in practice, not just in principle.
- Compiler-pass pipeline as the sole extension mechanism — every knowledge transformation is a `CompilerPass`; new passes register independently via a plugin-style registry, never by editing existing passes or the core pipeline.
- PydanticAI chosen as the concrete LLM adapter, kept entirely behind a domain-owned `LLMPort` — agents return validated Pydantic models directly, but the domain and compiler code never import `pydantic_ai`.

**Key decisions made during Phase 1 (Compiler Foundation):**
- **Diagnostics never halt the pipeline** — every registered pass runs to completion regardless of severity; the caller decides whether to fail after inspecting the full diagnostics list. This is deliberately Rust-compiler-style: no single buggy pass can mask diagnostics from later passes.
  - **Why:** matches the "structured diagnostics instead of side effects" principle already fixed in PROJECT.md/ARCHITECTURE.md.
- **Bad pass dependencies (unregistered names, cycles) are caught at pipeline-build time, not at registration time.** Registration happens via decorators, which are import-order-dependent — validating too early would break passes that self-register out of order.
- **The Cache abstraction stays generic** (opaque string key → value) in Phase 1; LLM-specific cache-key construction (checksum + prompt version + schema version + model id) is layered on top in Phase 2, not baked into the base Protocol.
- **The Artifact Manifest tracks only `artifact_id` + `version`** in Phase 1 — checksum and dependency-index tracking are deliberately deferred to Phase 5 (Incremental Compilation), avoiding speculative schema design.
- **`PassRegistry` uses stdlib `graphlib.TopologicalSorter`** rather than a hand-rolled dependency resolver.
- **`CompilerContext` is a frozen, slotted `dataclass`, not a Pydantic model** — it carries ports and run metadata but is never serialized, so Pydantic's validation/serialization machinery would be unneeded overhead.
- **`YamlFileRepository` rejects (raises `ValueError`) rather than sanitizes** path-traversal `artifact_id` values — the more defensive, auditable choice.

**Key decisions made during Phase 2 (Document Compiler):**
- **One combined LLM call per document**, not four separate calls for concepts/glossary/entities/references — cheaper, and joint context plausibly improves extraction accuracy.
  - **Phase:** 02-CONTEXT.md (D-02)
- **LLM extraction failures never hard-fail the compile.** After retries are exhausted, the Document IR is still produced with empty extraction fields plus a structured error `Diagnostic` — consistent with Phase 1's "diagnostics never halt the pipeline" decision.
  - **Phase:** 02-CONTEXT.md (D-03)
- **Sections are detected heading-based at any level (H1–H6)**; content preceding the first heading becomes an untitled preamble section.
- **Golden fixtures are small, hand-authored synthetic Markdown**, not real project documents — fast, deterministic, sufficient for pass-level unit testing (10 fixtures, Zephyr-framework domain).
- **`ExtractConceptsPass` result is typed `object` internally**, not the concrete PydanticAI return type — this is a deliberate seam that keeps `kir.llm` imports out of `kir.compiler`, verified by an AST-based import-boundary audit.
- **`LLMCachePort` was introduced as a dedicated Protocol** (distinct from the generic `CachePort`) after code review found `CompilerContext.llm_cache` was typed as the generic port but actually required `LLMCache`'s specific 4-argument interface — a real bug caught before it shipped.

**Key decision from Phase 2.1 (gap closure):**
- **`DocumentCompiler.compile()` was missing the actual call to `repository.save()`** — Phase 1 had proven `RepositoryPort` worked with fakes, and Phase 2 built the full extraction pipeline, but nothing wired the two together. This gap was invisible to both phases' own verification and only surfaced at the milestone-level integration audit. Phase 2.1 was inserted specifically to close it (STOR-01/STOR-02), and the review-fix cycle also rewrote a test that used two separate repositories (structurally incapable of detecting an id-collision) to share one repository instead, so a collision bug would actually be caught.

---

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 1 | Compiler Foundation | Complete (2026-06-30) | Domain model, ports, pass registry, and CompilerContext exist and are proven correct in isolation with fakes — zero LLM/filesystem/YAML imports in domain code. |
| 2 | Document Compiler | Complete (2026-07-01) | A single Markdown source compiles deterministically into a self-contained Document IR through four passes, including one LLM-backed extraction pass swappable between a fake and a real PydanticAI-backed adapter. |
| 2.1 | Close gap: STOR-01/STOR-02 (inserted) | Complete (2026-07-01) | `DocumentCompiler.compile()` now actually calls `repository.save()`, closing a persistence gap between Phase 1's proven `RepositoryPort` and Phase 2's compiler service that neither phase's own verification had caught. |

Total: 10 plans across 3 phases, all complete (4 in Phase 1, 5 in Phase 2, 1 in Phase 2.1).

---

## 4. Requirements Coverage

All 21 M1-scoped requirements are **satisfied** — cross-checked against three independent sources (phase VERIFICATION.md files, SUMMARY.md frontmatter, and the milestone audit's own re-derivation). Zero unsatisfied, zero orphaned.

**Compiler Foundation**
- ✅ CORE-01 — Domain model has zero import-level dependency on LLM/filesystem/YAML
- ✅ CORE-02 — Ports (LLMPort, RepositoryPort, MarkdownParserPort) exposed as typed Protocols
- ✅ CORE-03 — Passes register independently via plugin-style registry
- ✅ CORE-04 — Deterministic pipeline; execution order resolved from declared dependencies
- ✅ CORE-05 — All passes share one immutable CompilerContext
- ✅ CORE-06 — Passes return structured diagnostics, never print/log
- ✅ CORE-07 — Passes produce new immutable IR, never mutate in place

**Compiler Passes**
- ✅ PASS-01 — Every knowledge transformation is a CompilerPass
- ✅ PASS-02 — Each pass: exactly one IR in, one IR out
- ✅ PASS-03 — Passes deterministic and independently testable
- ✅ PASS-04 — Passes communicate only through IR + CompilerContext
- ✅ PASS-05 — Execution order derived from declared dependencies, not hardcoded

**Document Compiler**
- ✅ DOC-01 — Single Markdown source compiles into Document IR (id, title, source, checksum, language, sections, concepts, glossary, entities, references)
- ✅ DOC-02 — Two documents never cross-contaminate each other's Document IR
- ✅ DOC-03 — Extraction pass depends only on LLMPort, returns validated structured output

**LLM Adapter & Determinism**
- ✅ LLM-01 — PydanticAIAdapter satisfies LLMPort; fake and real adapters both swappable without touching pass code
- ✅ LLM-02 — Cache keyed on (checksum, prompt version, schema version, model id); unchanged input reproduces cached output with no re-call
- ✅ LLM-03 — Extraction pass unit-tested entirely against recorded/mocked responses; zero live API calls in CI

**Extensibility**
- ✅ EXT-01 — New passes registerable without modifying the core pipeline

**Storage**
- ✅ STOR-01 — Each artifact stored as one individual YAML file, no monolithic JSON
- ✅ STOR-02 — Generated `kir/` output written to a directory separate from raw sources (caller-enforced, no repository-level guard — see Tech Debt)

**Milestone audit verdict:** `tech_debt` — 21/21 requirements satisfied, all cross-phase integration points wired, E2E flow (`DocumentCompiler.compile()` → 4 passes → `repository.save()`) complete and code-verified, 123 tests passing with 0 failures. No blocking gaps; 14 non-blocking tech debt items recorded (see Section 6).

---

## 5. Key Decisions Log

| ID | Decision | Phase | Rationale |
|----|----------|-------|-----------|
| D-01 (Ph1) | Pipeline runs every pass to completion; halting is the caller's decision | 1 | Rust-compiler-style diagnostics — one bad pass shouldn't mask later diagnostics |
| D-02 (Ph1) | Bad dependency graphs caught at pipeline-build time, not registration time | 1 | Decorator registration is import-order-dependent |
| D-03 (Ph1) | Cache Protocol stays generic (no LLM-specific keys) in Phase 1 | 1 | Avoids coupling an abstraction to concerns that don't exist yet in this phase |
| D-04 (Ph1) | Artifact Manifest tracks only id + version in Phase 1 | 1 | Checksum/dependency-index tracking belongs to Phase 5 (incremental compilation) |
| — | `PassRegistry` built on stdlib `graphlib.TopologicalSorter` | 1 | No hand-rolled dependency resolver needed |
| — | `CompilerContext` is a frozen `dataclass`, not Pydantic | 1 | Never serialized — Pydantic validation/serialization would be unneeded overhead |
| — | `YamlFileRepository` rejects path-traversal `artifact_id`s (raises), doesn't sanitize | 1 | More defensive and auditable |
| D-01 (Ph2) | Sections detected heading-based at any level H1–H6 | 2 | Simple, predictable rule; pre-heading content becomes preamble |
| D-02 (Ph2) | One combined LLM call per document (concepts+glossary+entities+references) | 2 | Cheaper than 4 calls; joint context likely improves accuracy |
| D-03 (Ph2) | LLM extraction failure never hard-fails compile — empty fields + error Diagnostic | 2 | Consistent with Phase 1's D-01 diagnostics-never-halt principle |
| D-04 (Ph2) | Golden fixtures are small hand-authored synthetic Markdown | 2 | Fast, deterministic, sufficient for unit-level pass testing |
| — | `LLMCachePort` introduced as its own Protocol, distinct from generic `CachePort` | 2 | Code review caught a type mismatch between the generic port and `LLMCache`'s actual 4-kwarg interface (CR-02) |
| — | `ExtractConceptsPass` result typed `object` internally | 2 | Keeps `kir.llm` imports out of `kir.compiler` — hexagonal boundary enforced by AST audit |
| — | `DocumentCompiler.compile()` wired to call `repository.save()` | 2.1 | Closed a gap where Phase 1 proved `RepositoryPort` worked and Phase 2 built extraction, but nothing connected them — invisible to both phases' own verification, caught only at milestone audit |
| — | Two-document persistence test rewritten to share one repository | 2.1 | Original test used separate repositories, structurally unable to detect an id-collision bug (review-fix WR-03) |

---

## 6. Tech Debt & Deferred Items

Per the v1.0 milestone audit: **14 tech debt items, 0 critical, 5 warnings, 9 info.** None are blocking; the milestone verdict explicitly states "no action required before completing the milestone."

**Phase 1 — Compiler Foundation (5 items)**
- `CycleError` re-raise loses the structured `.args[1]` cycle-node list (warning)
- Dead code: `_DiagnosticsHolder` class in `tests/core/domain/test_diagnostic.py` (info)
- No empty-string/format validation on `ConceptId`, `Document.id`, `Conflict.id` (info)
- Import-boundary audit scans only `domain/`, not all of `core/` (info)
- 4 source files (`registry.py`, `base.py`, `cache_port.py`, `repository_port.py`) violate STYLE_GUIDE.md by using `from __future__ import annotations` / `TYPE_CHECKING` (warning)

**Phase 2 — Document Compiler (6 items)**
- `MarkdownItAdapter` strips code block content (fence/code_block tokens) → produces an empty Section (warning)
- Docstring contradiction in `extract_concepts.py` (info)
- Slugify collision risk on Unicode input with identical ASCII transliterations (info)
- Dead test code in the test suite (info)
- 25 occurrences of `from __future__ import annotations` / `TYPE_CHECKING` across test files, violating STYLE_GUIDE.md (warning)
- 02-VERIFICATION.md verifies DOC-01..03/LLM-01..03 implicitly through 9 truths rather than an explicit per-requirement-ID table (info)

**Phase 2.1 — Close gap (2 items)**
- No VALIDATION.md (Nyquist coverage plan) for this phase — understandable for a single-plan gap-closure phase, but noted
- STOR-02 has no repository-level guard preventing `output_dir == source_dir`; the separation is caller-enforced only, with no test at the repository level (warning)

**Cross-milestone (3 items)**
- REQUIREMENTS.md traceability table still shows "Pending" for all 21 completed M1 requirements — stale, should be corrected before/during archive
- ROADMAP.md progress table showed Phase 2.1 as "In progress" with an unchecked plan checkbox — stale (now corrected per the current ROADMAP.md state)

**Pending todos carried in STATE.md (not milestone-blocking):**
1. Add Google-style docstrings to all public APIs
2. Audit codebase against STYLE_GUIDE.md rules (the `from __future__ import annotations`/`TYPE_CHECKING` violations above are the concrete instance of this)
3. Upgrade to Python 3.14 and finalize type-hint strategy
4. Add use cases to README based on the "LLVM-for-knowledge" analogy

**Notable pattern from Phase 2's review:** all 3 critical bugs found during code review shared one root cause — `FakeLLMAdapter` ignores its input arguments, so tests never exercised the real prompt-rendering/cache-typing/null-handling code paths until manual review caught them. This is a real lesson for future phases: a fake that ignores its inputs can hide bugs that only a real (or input-sensitive fake) code path would surface.

---

## 7. Getting Started

- **Run the project:** No CLI exists yet (deliberately deferred to Phase 6, M3). The compiler is used programmatically today via `DocumentCompiler.compile(source_path)`.
- **Run tests:** `uv run pytest -q` (currently 123 tests passing, ~0.2s runtime — no live API calls, everything is fake/mocked per LLM-03).
- **Key directories:**
  - `src/kir/core/` — domain model (`domain/`), ports (`ports/`), pass registry (`passes/`), config (`config/`) — zero LLM/filesystem/YAML imports
  - `src/kir/compiler/documents/` — Phase 2's concrete passes (Parse, Section, Metadata, ExtractConcepts) and the `DocumentCompiler` service
  - `src/kir/llm/` — the only package that imports `pydantic_ai`: `PydanticAIAdapter`, `FakeLLMAdapter`, `LLMCache`, `PromptRegistry`, and versioned prompt templates (`prompts/extract_v1.md`)
  - `src/kir/tooling/repository/` — `YamlFileRepository`, the first real (non-fake) adapter, one YAML file per artifact
- **Where to look first:**
  - `src/kir/core/passes/registry.py` — the `PassRegistry`/pipeline mechanics (topological sort via stdlib `graphlib`)
  - `src/kir/compiler/documents/compiler.py` — the E2E flow: read → parse → section → metadata → extract → save
  - `.planning/PROJECT.md` — product definition, architecture principles, product boundary
  - `.planning/ROADMAP.md` — current milestone's phase detail (rewritten per milestone)
  - `.planning/REQUIREMENTS.md` — full requirement set by milestone (M1/M2/M3)
  - `.planning/v1.0-MILESTONE-AUDIT.md` — the authoritative verification record for this milestone
- **Tech stack:** Python 3.13+, Pydantic v2, PydanticAI (behind `LLMPort`), markdown-it-py, ruamel.yaml, uv, Ruff, Pytest (+ pytest-asyncio).

---

## Stats

- **Timeline:** 2026-06-29 (project init/planning) → 2026-07-01 (Phase 2.1 verified) — 3 calendar days
- **Phases:** 3 / 3 complete (1, 2, 2.1)
- **Plans:** 10 / 10 complete
- **Commits:** 120 total in repo; ~58 tied directly to phase execution artifacts
- **Files changed (full history):** 182 files (+17,309 / −0 insertions/deletions — greenfield project)
- **Tests:** 123 passing, 0 failures, ~0.2s runtime
- **Tech debt:** 14 items (0 critical, 5 warnings, 9 info) — none blocking
- **Contributors:** mniedre

---

*This summary was generated from `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/v1.0-MILESTONE-AUDIT.md`, and all Phase 1/2/2.1 CONTEXT/SUMMARY/VERIFICATION/LEARNINGS/REVIEW artifacts under `.planning/phases/`.*
