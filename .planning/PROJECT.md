# KIR (Knowledge Intermediate Representation)

## Product Definition

KIR is a semantic compiler that transforms heterogeneous raw sources (starting with Markdown) into Knowledge IR — a canonical, deterministic, provenance-tracked semantic representation of knowledge. It is explicitly not a wiki, note-taking app, or graph/search/vector database: KIR's public API ends at Knowledge IR, and any rendering, sync, or visualization into Logseq/Obsidian/Notion/graph DBs/search indexes is the responsibility of downstream consumers. Think of it as "LLVM, but for knowledge" — a compiler with a stable IR and a pipeline of independently testable passes.

## Core Value

Given identical raw sources, compiler version, prompt version, and schema version, KIR must deterministically compile raw Markdown into a canonical Knowledge IR that merges concepts/relations/taxonomy across documents, preserves full provenance, and explicitly records (never silently resolves) semantic conflicts.

## Architecture Principles

1. KIR is a Semantic Compiler.
2. Knowledge IR is the only canonical model.
3. Compilation is deterministic.
4. Compilation is incremental.
5. Compiler passes are independent.
6. The domain model depends on nothing (no LLM SDK, no filesystem, no YAML library).
7. Infrastructure (adapters) depends on the domain — never the reverse.
8. Rendering, synchronization, and querying are outside KIR.
9. LLMs perform semantic analysis only — they never modify repository structure directly.
10. Knowledge IR is stable: source formats, LLM providers, and downstream consumers can change without changing the Knowledge IR schema.

## Product Boundary

```
Raw Sources (Markdown)
      ↓
  Document Compiler
      ↓
  Document IR
      ↓
  Knowledge Compiler
      ↓
  Knowledge IR
══════════════════════  ← KIR's public API ends here
      ↓
  (downstream, out of scope for KIR)
      ↓
  Synchronization / Rendering Agent
      ↓
  Logseq · Obsidian · Notion · Search Index · Graph DB · LLM context
```

Everything above the line is KIR. Everything below it is a downstream consumer's responsibility — KIR neither builds nor depends on any of it.

## Milestones

KIR's full v1 scope is delivered across three milestones. This is the long-lived, rarely-changing product-evolution view — the **current** milestone's detailed phase plan lives in `.planning/ROADMAP.md`, which is rewritten when a milestone completes rather than accumulating every future milestone's detail up front.

| Milestone | Delivers | Phases (when active) |
|-----------|----------|----------------------|
| **M1 — Deterministic Document Compiler** (current) | Domain model, ports, pass-registry mechanics, and a working Markdown → Document IR pipeline (deterministic passes + one LLM-backed extraction pass) | Phase 1: Compiler Foundation, Phase 2: Document Compiler |
| **M2 — Canonical Knowledge Compiler** | Multi-document merge: aliases, canonical concepts, relations, taxonomy, conflict detection; full pipeline proven correct on tiered reference corpora | Phase 3: Knowledge Compiler, Phase 4: Validation |
| **M3 — Production Semantic Compiler** | Incremental compilation, `kir compile` CLI, real-corpus acceptance | Phase 5: Incremental Compilation, Phase 6: CLI & Real-Corpus Acceptance |

**How this works:** ROADMAP.md currently contains only M1's phases (1–2) in full planning detail. M2 and M3 are intentionally *not* detailed in ROADMAP.md yet. When M1 completes (via `/gsd-complete-milestone`), ROADMAP.md is rewritten for M2's phases (3–4), and so on. The full set of v1 requirements is already defined in REQUIREMENTS.md (split into M1/M2/M3 sections) so nothing is lost — only the detailed phase/plan breakdown for M2/M3 is deferred until its milestone becomes current.

## Architecture & Workstreams

This is the persistent architectural shape of the system — independent technical subsystems that cut across milestones and phases. It changes rarely, unlike the roadmap.

| Workstream | Scope |
|------------|-------|
| **A — Core** | Domain Model (Concept, Relation, Taxonomy, Document), Ports (LLMPort, RepositoryPort, MarkdownParserPort), Pass API, CompilerContext |
| **B — Document Compiler** | Markdown Parser, Metadata extraction, Section Parser, Document IR assembly |
| **C — Knowledge Compiler** | Alias resolution, Concept Merge, Relations, Taxonomy, Conflict detection |
| **D — Tooling** | Storage/Repository adapter, CLI, Validation infrastructure, Tests |
| **E — LLM Infrastructure** | Structured Output, Prompt Registry, Prompt Versioning, Provider Adapter, Caching, Replay Tests |

Workstream E is called out separately from Workstream B even though both land primarily in the Document Compiler milestone, because LLM Infrastructure (prompt registry/versioning, swappable provider adapter, response caching, replay-based tests) is substantial standalone infra with its own correctness concerns (determinism, cache-key construction, adapter substitutability) — distinct from Markdown parsing and Document IR assembly.

**Cross-cutting concern — The Artifact System:** Several requirements spanning multiple phases form one coherent thread: how a compiled artifact is structured, identified, versioned, and tracked for dependency purposes (Artifact → Metadata → Manifest → Versions → Checksum → Dependencies). Not a separate workstream, but worth keeping visible: Artifact/Manifest structure (Phase 1) → Checksum for LLM cache keys (Phase 2) → Versions + Pass manifest (Phase 4) → Dependency index for incremental scoping (Phase 5).

Any concrete unit of work sits at the intersection of a milestone (which phase) and a workstream (which subsystem) — this is what `/gsd-plan-phase` can use to identify which units of work inside a phase are genuinely independent and can be planned/executed in parallel.

## Requirements

See `.planning/REQUIREMENTS.md` — the single source of truth for what KIR builds, organized by milestone (M1 current / M2, M3 future) plus v2 deferred and Out of Scope. Not duplicated here to avoid two sources of truth; this document evolves rarely, requirements evolve per phase.

## Acceptance Corpus

The user's real-world test corpus is a 700-article Markdown export from Slab. It is used in two tiers per REQUIREMENTS.md: tiny (~5 docs) and medium (~50 docs) synthetic/representative fixtures gate CI on every commit (M2, ACC-01); the full 700-document Slab export is the on-demand, real-world acceptance run that defines v1 "done" (M3, ACC-02).

## Context

- The user has already sketched a preferred technical direction (see Architectural Decisions) — these are strong priors from the user's own design work, not decisions imposed by research, and should be respected unless they create a real conflict during planning.
- Hexagonal architecture intent: the domain model (Concept, Relation, Taxonomy, Document) has zero knowledge of OpenAI/Anthropic SDKs, the filesystem, or YAML — those live behind adapters (LLM Adapter, Repository, Parser).

## Constraints

- **Tech stack**: Python 3.13+, Pydantic v2, Typer (CLI), Ruff, Pytest, uv — user's explicit choice, rationale: strong YAML/LLM ergonomics and fast prototyping outweigh raw performance, which is not a bottleneck for a knowledge compiler
- **LLM integration**: LLM-backed passes depend only on a domain-owned LLMPort; the concrete LLM library (e.g. PydanticAI) is an interchangeable adapter detail, never a domain dependency
- **Determinism**: identical inputs (raw sources + compiler/schema/prompt versions) must always produce identical Knowledge IR — this rules out any non-pinned or non-recorded LLM call
- **Storage format**: one YAML file per artifact, never monolithic JSON — required for git-friendliness and human readability
- **Scale**: must handle the user's real 700-document corpus end-to-end for v1 to be considered done

## Architectural Decisions

Decisions already made, not pending evaluation:

- Python 3.13+ / Pydantic v2 / Typer / Ruff / Pytest / uv — best YAML + LLM ergonomics, fast MVP iteration; raw speed isn't a bottleneck for this workload
- Pydantic v2 models as the canonical IR representation — free schema validation, JSON/YAML (de)serialization, and versioning support
- Hexagonal architecture (domain core isolated from LLM/filesystem adapters) — keeps Knowledge IR schema stable regardless of LLM provider or storage backend changes
- Tactical DDD only (Entities/Value Objects/Aggregates, no Event Sourcing) — enough structure to model Concept/Relation/Taxonomy cleanly without enterprise overhead
- Compiler-pass pipeline as the core extension mechanism — new passes register independently; matches the LLVM-for-knowledge mental model
- PydanticAI as the concrete LLM adapter implementation, behind LLMPort — agents return validated Pydantic models directly, with no manual parsing/validation glue, while staying swappable
- Concept identity is a defined rule, not a frozen algorithm (candidate: name-slug, finalized during Phase 3 planning) — slug-of-name alone breaks on renames (e.g. "OAuth" → "OAuth 2.1"); the requirement is stable, rule-defined identity
- Relation vocabulary is core-and-extensible, not closed — a hardcoded closed vocabulary would force requirement rewrites every time a real new relation type (e.g. authenticates_with, deprecated_by) is needed
- Raw sources and kir/ output kept in separate directories, raw never mutated — preserves provenance integrity and keeps the compiler side-effect-free on inputs
- Incremental compilation via per-document checksum diffing, sequenced after correctness is proven (M3, not earlier) — simplest correct mechanism at this scale; avoids optimizing around dependencies that aren't yet well understood
- LLM passes tested via recorded/mocked responses, not live API calls — fast, repeatable, free CI; determinism requirement makes live-API tests unreliable anyway

---
*Last updated: 2026-06-29 after restructuring per user feedback: renamed "What This Is" to "Product Definition," added Architecture Principles and Product Boundary diagram, moved Requirements to a pointer at REQUIREMENTS.md (removing the duplicate Active/Validated/Out-of-Scope lists), renamed Key Decisions to Architectural Decisions (dropped the Outcome/Pending column — these are decisions, not open questions), moved the Slab corpus mention into a new Acceptance Corpus section, and moved the Evolution/process-instruction section to `.planning/PROCESS.md`.*
