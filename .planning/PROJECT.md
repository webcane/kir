# KIR (Knowledge Intermediate Representation)

## What This Is

KIR is a semantic compiler that transforms heterogeneous raw sources (starting with Markdown) into Knowledge IR — a canonical, deterministic, provenance-tracked semantic representation of knowledge. It is explicitly not a wiki, note-taking app, or graph/search/vector database: KIR's public API ends at Knowledge IR, and any rendering, sync, or visualization into Logseq/Obsidian/Notion/graph DBs/search indexes is the responsibility of downstream consumers. Think of it as "LLVM, but for knowledge" — a compiler with a stable IR and a pipeline of independently testable passes.

## Core Value

Given identical raw sources, compiler version, prompt version, and schema version, KIR must deterministically compile raw Markdown into a canonical Knowledge IR that merges concepts/relations/taxonomy across documents, preserves full provenance, and explicitly records (never silently resolves) semantic conflicts.

## Milestones

KIR's full v1 scope is delivered across three milestones. This is the long-lived, rarely-changing product-evolution view — the **current** milestone's detailed phase plan lives in `.planning/ROADMAP.md`, which is rewritten when a milestone completes rather than accumulating every future milestone's detail up front.

| Milestone | Delivers | Phases (when active) |
|-----------|----------|----------------------|
| **M1 — Deterministic Document Compiler** (current) | Domain model, ports, pass-registry mechanics, and a working Markdown → Document IR pipeline (deterministic passes + one LLM-backed extraction pass) | Phase 1: Compiler Foundation, Phase 2: Document Compiler |
| **M2 — Canonical Knowledge Compiler** | Multi-document merge: aliases, canonical concepts, relations, taxonomy, conflict detection; full pipeline proven correct on tiered reference corpora | Phase 3: Knowledge Compiler, Phase 4: Validation |
| **M3 — Production Semantic Compiler** | Incremental compilation, `kir compile` CLI, real 700-doc Slab corpus acceptance | Phase 5: Incremental Compilation, Phase 6: CLI & Real-Corpus Acceptance |

**How this works:** ROADMAP.md currently contains only M1's phases (1–2) in full planning detail (goals, success criteria, plans). M2 and M3 are intentionally *not* detailed in ROADMAP.md yet — planning that detail now would mean `/gsd-plan-phase` and execution agents carry phases that are months away and may still shift. When M1 completes (via `/gsd-complete-milestone`), ROADMAP.md is rewritten for M2's phases (3–4), and so on. The full set of 42 v1 requirements is already defined in REQUIREMENTS.md (split into "M1 — Current Roadmap Scope" and "M2/M3 — Future Milestone Scope, Already Defined") so nothing is lost — only the detailed phase/plan breakdown for M2/M3 is deferred until its milestone becomes current.

## Architecture & Workstreams

This is the persistent architectural shape of the system — independent technical subsystems that cut across milestones and phases. It changes rarely, unlike the roadmap.

| Workstream | Scope |
|------------|-------|
| **A — Core** | Domain Model (Concept, Relation, Taxonomy, Document), Ports (LLMPort, RepositoryPort, MarkdownParserPort), Pass API, CompilerContext |
| **B — Document Compiler** | Markdown Parser, Metadata extraction, Section Parser, Document IR assembly |
| **C — Knowledge Compiler** | Alias resolution, Concept Merge, Relations, Taxonomy, Conflict detection |
| **D — Tooling** | Storage/Repository adapter, CLI, Validation infrastructure, Tests |
| **E — LLM Infrastructure** | Structured Output, Prompt Registry, Prompt Versioning, Provider Adapter, Caching, Replay Tests |

Workstream E is called out separately from Workstream B even though both land primarily in the Document Compiler milestone, because LLM Infrastructure (prompt registry/versioning, swappable provider adapter, response caching, replay-based tests) is substantial standalone infra with its own correctness concerns (determinism, cache-key construction, adapter substitutability) — distinct from Markdown parsing and Document IR assembly. Treating them as one undifferentiated blob is a known failure mode to avoid.

**Cross-cutting concern — The Artifact System:** Several requirements spanning multiple phases form one coherent thread: how a compiled artifact is structured, identified, versioned, and tracked for dependency purposes (Artifact → Metadata → Manifest → Versions → Checksum → Dependencies). Not a separate workstream, but worth keeping visible: Artifact/Manifest structure (Phase 1) → Checksum for LLM cache keys (Phase 2) → Versions + Pass manifest (Phase 4) → Dependency index for incremental scoping (Phase 5).

Any concrete unit of work sits at the intersection of a milestone (which phase) and a workstream (which subsystem) — this is what `/gsd-plan-phase` can use to identify which units of work inside a phase are genuinely independent and can be planned/executed in parallel.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Document Compiler parses Markdown sources into Document IR (id, title, source, checksum, language, sections, concepts, glossary, entities, references) without merging across documents
- [ ] Knowledge Compiler merges multiple Document IR artifacts into Knowledge IR (canonical concepts, aliases, definitions, taxonomy, relations, provenance, conflicts)
- [ ] Concept model stores id, canonical name, aliases, definition, category, taxonomy path, relations, provenance, and source documents
- [ ] Concept IDs are derived as a slug of the canonical name and remain stable across compiler runs
- [ ] Relations are first-class explicit semantic objects (related_to, depends_on, part_of, implements, extends, replaces, uses, contains) — never inferred from presentation/formatting
- [ ] Taxonomy is modeled independently of folders/filenames/source hierarchy
- [ ] Every semantic element (concept, definition, relation) preserves provenance: source document + section
- [ ] Compiler pipeline is implemented as a sequence of independently testable passes (Parse → Section → Metadata → ExtractConcepts(LLM) → ResolveAliases → MergeConcepts → BuildRelations → BuildTaxonomy → Conflict), each consuming one IR and producing one IR
- [ ] Adding a new pass does not require modifying existing passes (pass registration mechanism)
- [ ] Semantic-analysis passes (concept extraction, alias detection, definition generation, taxonomy classification, relation extraction) are LLM-backed and provider-agnostic via PydanticAI, returning validated Pydantic models
- [ ] Conflict detection covers duplicate concepts, conflicting definitions, taxonomy conflicts, alias conflicts, orphan concepts, and circular semantic relations
- [ ] Conflicts are recorded as first-class YAML artifacts (never silently auto-resolved)
- [ ] Incremental compilation: per-source-document checksum comparison determines which Document IR artifacts need rebuilding, and only the affected Knowledge IR is re-merged
- [ ] Every generated artifact records compiler version, schema version, and prompt version
- [ ] Repository layout stores each artifact as an individual YAML file (documents/, concepts/, relations/, taxonomy/, aliases/, metadata/) — no monolithic JSON
- [ ] Raw sources and generated kir/ output live in separate directories within the same repo; raw sources are never mutated
- [ ] `kir compile` CLI command runs the full pipeline end-to-end
- [ ] Deterministic passes are unit-tested directly; LLM-backed passes are tested against recorded/mocked LLM responses (golden fixtures)
- [ ] v1 acceptance bar: full compile (raw → Document IR → Knowledge IR) succeeds end-to-end on the user's real 700-document Slab Markdown export, with conflicts and provenance correctly recorded

### Out of Scope

- Rendering Knowledge IR into any wiki/workspace format (Logseq, Obsidian, Notion, Markdown notes) — explicitly a downstream consumer's responsibility, not KIR's
- Synchronizing or writing back to external systems — KIR is one-directional: raw → IR
- Graph visualization, graph database storage, or search indexing — downstream concerns
- Vector database / embedding storage — downstream concern, not part of the canonical semantic model
- Note organization, folder structure, or any wiki-like UX — KIR has no concept of "notes"
- HTML, PDF, or other non-Markdown source parsers — deferred until Markdown pipeline is proven at the 700-doc scale
- `doctor` and `stats` CLI commands — deferred past v1; only `compile` ships now
- Silent automatic conflict resolution — conflicts are always recorded, never resolved without explicit human/LLM-assisted review (by design, permanent, not just a v1 deferral)
- Event Sourcing or full enterprise DDD tooling — only tactical DDD patterns (Entities, Value Objects, Aggregates) are used; explicitly rejected as unneeded complexity

## Context

- The user has a real-world test corpus: a 700-article Markdown export from Slab, which is the concrete target for v1's acceptance bar.
- Architectural philosophy is explicitly compiler-style (LLVM analogy): Knowledge IR is the stable interface; raw source formats, LLM providers, and downstream consumers must all be able to change without touching the Knowledge IR schema.
- The user has already sketched a preferred technical direction (see Key Decisions) — these are strong priors from the user's own design work, not decisions imposed by research, and should be respected unless they create a real conflict during planning.
- Hexagonal architecture intent: the domain model (Concept, Relation, Taxonomy, Document) has zero knowledge of OpenAI/Anthropic SDKs, the filesystem, or YAML — those live behind adapters (LLM Adapter, Repository, Parser).

## Constraints

- **Tech stack**: Python 3.13+, Pydantic v2, Typer (CLI), Ruff, Pytest, uv — user's explicit choice, rationale: strong YAML/LLM ergonomics and fast prototyping outweigh raw performance, which is not a bottleneck for a knowledge compiler
- **LLM integration**: must be provider-agnostic via PydanticAI so the semantic-analysis passes aren't locked to a single vendor
- **Determinism**: identical inputs (raw sources + compiler/schema/prompt versions) must always produce identical Knowledge IR — this rules out any non-pinned or non-recorded LLM call
- **Storage format**: one YAML file per artifact, never monolithic JSON — required for git-friendliness and human readability
- **Scale**: must handle the user's real 700-document corpus end-to-end for v1 to be considered done

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python 3.13+ / Pydantic v2 / Typer / Ruff / Pytest / uv | Best YAML + LLM ergonomics, fast MVP iteration; raw speed isn't a bottleneck for this workload | — Pending |
| Pydantic v2 models as the canonical IR representation | Free schema validation, JSON/YAML (de)serialization, and versioning support | — Pending |
| Hexagonal architecture (domain core isolated from LLM/filesystem adapters) | Keeps Knowledge IR schema stable regardless of LLM provider or storage backend changes | — Pending |
| Tactical DDD only (Entities/Value Objects/Aggregates, no Event Sourcing) | Enough structure to model Concept/Relation/Taxonomy cleanly without enterprise overhead | — Pending |
| Compiler-pass pipeline as the core extension mechanism | New passes register independently; matches the LLVM-for-knowledge mental model | — Pending |
| PydanticAI for LLM-backed passes | Agents return validated Pydantic models directly — no manual parsing/validation glue | — Pending |
| Concept identity is a defined rule, not a frozen algorithm (candidate: name-slug, revisited during planning) | Slug-of-name alone breaks on renames (e.g. "OAuth" → "OAuth 2.1"); the requirement is stable, rule-defined identity, leaving the exact mechanism an implementation decision made during planning | — Pending |
| Relation vocabulary is core-and-extensible, not closed | A hardcoded closed vocabulary would force requirement rewrites every time a real new relation type (e.g. authenticates_with, deprecated_by) is needed; core vocabulary + documented extension policy avoids that churn | — Pending |
| LLM passes depend only on a domain-owned LLMPort, never directly on PydanticAI or any SDK | Keeps the concrete LLM library an interchangeable adapter detail, consistent with the hexagonal-architecture decision below — a stack change shouldn't ripple into pass logic | — Pending |
| Raw sources and kir/ output kept in separate directories, raw never mutated | Preserves provenance integrity and keeps the compiler side-effect-free on inputs | — Pending |
| Incremental compilation via per-document checksum diffing | Simplest correct mechanism for hundreds-of-documents scale; avoids full-corpus recompilation cost | — Pending |
| LLM passes tested via recorded/mocked responses, not live API calls | Fast, repeatable, free CI; determinism requirement makes live-API tests unreliable anyway | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-29 after initialization*
